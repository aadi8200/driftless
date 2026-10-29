import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from core.models import (
    UsageLog,
    UserSettings,
    SiteLimit,
    CategoryOverride,
    FocusSession,
    clean_domain,
    classify_domain,
    CATEGORY_PRODUCTIVITY,
    CATEGORY_SOCIAL,
    CATEGORY_ENTERTAINMENT,
    CATEGORY_OTHER
)


class DriftlessModelAndHelperTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='password123')

    def test_clean_domain(self):
        self.assertEqual(clean_domain('https://www.youtube.com/watch?v=123'), 'youtube.com')
        self.assertEqual(clean_domain('http://github.com:8000/profile'), 'github.com')
        self.assertEqual(clean_domain('  INSTAGRAM.COM/  '), 'instagram.com')
        self.assertEqual(clean_domain(''), '')

    def test_classification_logic(self):
        # Productive defaults
        self.assertEqual(classify_domain('github.com'), CATEGORY_PRODUCTIVITY)
        self.assertEqual(classify_domain('cs.stanford.edu'), CATEGORY_PRODUCTIVITY)
        self.assertEqual(classify_domain('iitb.ac.in'), CATEGORY_PRODUCTIVITY)
        
        # Social & Entertainment
        self.assertEqual(classify_domain('instagram.com'), CATEGORY_SOCIAL)
        self.assertEqual(classify_domain('netflix.com'), CATEGORY_ENTERTAINMENT)
        
        # Fallback to Other
        self.assertEqual(classify_domain('randomunknownblog.xyz'), CATEGORY_OTHER)

    def test_user_category_override(self):
        # Overriding a social domain to Productive for this user
        CategoryOverride.objects.create(
            user=self.user,
            domain='instagram.com',
            category=CATEGORY_PRODUCTIVITY
        )
        self.assertEqual(classify_domain('instagram.com', user=self.user), CATEGORY_PRODUCTIVITY)


class DriftlessApiAndDataIsolationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(username='alice', password='password123')
        self.user_b = User.objects.create_user(username='bob', password='password123')

        self.token_a = Token.objects.create(user=self.user_a)
        self.token_b = Token.objects.create(user=self.user_b)

    def test_registration_and_persona_defaults(self):
        res = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'password': 'password123',
            'persona': 'student'
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertIn('token', res.data)
        
        new_u = User.objects.get(username='newuser')
        limits = SiteLimit.objects.filter(user=new_u)
        self.assertTrue(limits.exists(), "Persona preset limits should be applied on registration")

    def test_per_user_data_isolation_limits(self):
        # User A creates a limit
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        res_a = self.client.post('/api/limits/', {
            'domain': 'reddit.com',
            'daily_limit_minutes': 25
        }, format='json')
        self.assertEqual(res_a.status_code, 201)
        limit_id = res_a.data['id']

        # User B queries limits — must NOT see User A's limit
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_b.key}')
        res_b = self.client.get('/api/limits/')
        self.assertEqual(res_b.status_code, 200)
        self.assertEqual(len(res_b.data), 0)

        # User B cannot modify or delete User A's limit
        res_del = self.client.delete(f'/api/limits/{limit_id}/')
        self.assertEqual(res_del.status_code, 404)
        self.assertTrue(SiteLimit.objects.filter(id=limit_id).exists())

    def test_per_user_data_isolation_usage_and_summary(self):
        today = datetime.date.today().isoformat()

        # Alice logs productive time
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        self.client.post('/api/usage/', [{
            'website_url': 'github.com',
            'time_spent_seconds': 3600,
            'date': today
        }], format='json')

        # Bob logs social time
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_b.key}')
        self.client.post('/api/usage/', [{
            'website_url': 'instagram.com',
            'time_spent_seconds': 1200,
            'date': today
        }], format='json')

        # Check Alice's summary
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        summary_a = self.client.get('/api/summary/').data
        self.assertEqual(summary_a['stats']['productive_seconds'], 3600)
        self.assertEqual(summary_a['stats']['social_seconds'], 0)
        self.assertEqual(summary_a['stats']['focus_efficiency'], 100)

        # Check Bob's summary
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_b.key}')
        summary_b = self.client.get('/api/summary/').data
        self.assertEqual(summary_b['stats']['productive_seconds'], 0)
        self.assertEqual(summary_b['stats']['social_seconds'], 1200)
        self.assertEqual(summary_b['stats']['focus_efficiency'], 0)

    def test_token_regeneration(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        res = self.client.post('/api/auth/regenerate-token/')
        self.assertEqual(res.status_code, 200)
        new_token = res.data['token']
        self.assertNotEqual(new_token, self.token_a.key)

        # Old token is rejected
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        res_old = self.client.get('/api/summary/')
        self.assertEqual(res_old.status_code, 401)

        # New token works
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {new_token}')
        res_new = self.client.get('/api/summary/')
        self.assertEqual(res_new.status_code, 200)

    def test_three_categories_classification(self):
        # 1. Productive site from allowed_sites list
        settings = UserSettings.objects.create(
            user=self.user_a,
            allowed_sites='github.com\ncustomworksite.org',
            blocked_sites='instagram.com\ncustomfun.xyz'
        )
        self.assertEqual(classify_domain('customworksite.org', user=self.user_a), 'Productive sites')
        self.assertEqual(classify_domain('customfun.xyz', user=self.user_a), 'Distracting sites')
        self.assertEqual(classify_domain('unknownunrelated.com', user=self.user_a), 'Others')

    def test_site_lists_and_limits_summary(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        settings = UserSettings.objects.create(
            user=self.user_a,
            blocked_sites='reddit.com\nyoutube.com',
            allowed_sites='github.com',
            daily_limit_minutes=45
        )

        # Set custom limit on reddit.com = 15m
        self.client.post('/api/limits/', {
            'domain': 'reddit.com',
            'daily_limit_minutes': 15,
            'enabled': True
        }, format='json')

        # Log 6m on reddit.com
        today = datetime.date.today().isoformat()
        self.client.post('/api/usage/', [{
            'website_url': 'reddit.com',
            'time_spent_seconds': 360,
            'date': today
        }], format='json')

        # Summary check
        res = self.client.get('/api/summary/')
        self.assertEqual(res.status_code, 200)
        data = res.data

        # Check distractions list: reddit.com has custom limit 15m, 6m used
        reddit_entry = next((d for d in data['distractions'] if d['website_url'] == 'reddit.com'), None)
        self.assertIsNotNone(reddit_entry)
        self.assertEqual(reddit_entry['used_minutes'], 6)
        self.assertEqual(reddit_entry['limit_minutes'], 15)

        # youtube.com uses global default 45m, 0m used
        youtube_entry = next((d for d in data['distractions'] if d['website_url'] == 'youtube.com'), None)
        self.assertIsNotNone(youtube_entry)
        self.assertEqual(youtube_entry['used_minutes'], 0)
        self.assertEqual(youtube_entry['limit_minutes'], 45)

        # Verify weekly categories
        self.assertIn('productive_seconds', data['weekly'][0])
        self.assertIn('distracting_seconds', data['weekly'][0])
        self.assertIn('others_seconds', data['weekly'][0])

    def test_scheduled_focus_mode_settings(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        
        # Initial GET
        res = self.client.get('/api/settings/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('schedule_enabled', res.data)
        self.assertIn('schedule_start', res.data)
        self.assertIn('schedule_end', res.data)

        # PATCH update schedule
        patch_res = self.client.patch('/api/settings/', {
            'schedule_enabled': True,
            'schedule_start': '21:30',
            'schedule_end': '23:45',
        }, format='json')
        self.assertEqual(patch_res.status_code, 200)
        self.assertTrue(patch_res.data['schedule_enabled'])
        self.assertEqual(patch_res.data['schedule_start'], '21:30')
        self.assertEqual(patch_res.data['schedule_end'], '23:45')

        # Verify persisted in DB
        settings = UserSettings.objects.get(user=self.user_a)
        self.assertTrue(settings.schedule_enabled)
        self.assertEqual(settings.schedule_start, '21:30')
        self.assertEqual(settings.schedule_end, '23:45')

    def test_green_grove_summary(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_a.key}')
        settings = UserSettings.objects.create(
            user=self.user_a,
            daily_limit_minutes=30
        )
        SiteLimit.objects.create(
            user=self.user_a,
            domain='youtube.com',
            daily_limit_minutes=20,
            enabled=True
        )

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)

        # Day -2: Successful day (spent 10m on youtube.com, limit is 20m) -> 'grown'
        UsageLog.objects.create(
            user=self.user_a,
            website_url='youtube.com',
            time_spent_seconds=600,
            date=two_days_ago
        )

        # Day -1: Exceeded limit (spent 25m on youtube.com, limit is 20m) -> 'withered'
        UsageLog.objects.create(
            user=self.user_a,
            website_url='youtube.com',
            time_spent_seconds=1500,
            date=yesterday
        )

        res = self.client.get('/api/summary/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('grove', res.data)
        grove = res.data['grove']
        self.assertEqual(len(grove['days']), 30)

        # Find status for day -2 and day -1
        day_minus_2 = next((d for d in grove['days'] if d['date'] == two_days_ago.isoformat()), None)
        day_minus_1 = next((d for d in grove['days'] if d['date'] == yesterday.isoformat()), None)

        self.assertIsNotNone(day_minus_2)
        self.assertEqual(day_minus_2['status'], 'grown')

        self.assertIsNotNone(day_minus_1)
        self.assertEqual(day_minus_1['status'], 'withered')

        self.assertGreaterEqual(grove['total_grown'], 1)


