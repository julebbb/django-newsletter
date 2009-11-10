import datetime
import time

from django.core import mail

from django.core.urlresolvers import reverse

from newsletter.models import *
from newsletter.forms import *

from utils import *

class WebSubscribeTestCase(WebTestCase, MailTestCase):
    def setUp(self):
        self.n = Newsletter(title='Test newsletter',
                            slug='test-newsletter',
                            sender='Test Sender',
                            email='test@testsender.com')
        self.n.save()
        self.n.site = get_default_sites()
        
        self.subscribe_url = reverse('newsletter_subscribe_request', 
                                     kwargs={'newsletter_slug' : self.n.slug })
                                     
        self.unsubscribe_url = reverse('newsletter_unsubscribe_request', 
                                       kwargs={'newsletter_slug' : self.n.slug })
                                       
        self.unsubscribe_url = reverse('newsletter_unsubscribe_request', 
                                  kwargs={'newsletter_slug' : self.n.slug })
        
        super(WebSubscribeTestCase, self).setUp()
    
    def test_urls(self):
        self.assert_(len(self.subscribe_url))
        self.assert_(len(self.unsubscribe_url))
        self.assert_(len(self.unsubscribe_url))
    
    def test_subscribe_request_view(self):
        """ Test the subscription form. """
        r = self.client.get(self.subscribe_url)
        
        self.assertContains(r, self.n.title, status_code=200)
        self.assertContains(r, 'input id="id_name_field" type="text" name="name_field"')
        self.assertContains(r, 'input id="id_email_field" type="text" name="email_field"')
        
        self.assertEqual(r.context['newsletter'], self.n)
    
    def test_subscribe_request_post(self):
        """ Post the subscription form. """
        r = self.client.post(self.subscribe_url, {'name_field':'Test Name', 'email_field':'test@email.com'})
        
        self.assertContains(r, self.n.title, status_code=200)
        self.assertNotContains(r, 'input id="id_name_field" type="text" name="name"')
        self.assertNotContains(r, 'input id="id_email_field" type="text" name="email"')
        
        self.assertInContext(r, 'newsletter', Newsletter, self.n)
        self.assertInContext(r, 'form', SubscribeRequestForm)
        
        subscription = getattr(r.context['form'], 'instance', None)
        self.assert_(subscription)
        self.assertFalse(subscription.subscribed)
        self.assertFalse(subscription.unsubscribed)
        
        """ Check the subscription email. """
        self.assertEquals(len(mail.outbox), 1)
                
        activate_url = subscription.subscribe_activate_url()
        full_activate_url = 'http://%s%s' % (self.site.domain, activate_url)
        
        self.assertEmailContains(full_activate_url)
    
    def test_subscribe_request_activate(self):
        """ Test subscription activation. """
        subscription = Subscription(newsletter=self.n, name='Test Name', email='test@email.com')
        subscription.save()
        
        WAIT_TIME=2
        time.sleep(WAIT_TIME)
        
        self.assertFalse(subscription.subscribed)
        
        activate_url = subscription.subscribe_activate_url()
        self.assert_(activate_url)

        r = self.client.get(activate_url)
        self.assertInContext(r, 'form', UpdateForm)
        self.assertContains(r, subscription.activation_code)
        
        r = self.client.post(activate_url, {'name_field':'Test Name', 'email_field':'test@email.com', 'user_activation_code':subscription.activation_code})        
        self.assertInContext(r, 'form', UpdateForm)
        
        #subscription = Subscription.objects.get(pk=subscription.pk)
        subscription = getattr(r.context['form'], 'instance', None)
        self.assert_(subscription)
        self.assert_(subscription.subscribed)
        self.assertFalse(subscription.unsubscribed)
        
        dt = (subscription.subscribe_date - subscription.create_date).seconds
        self.assert_(dt >= WAIT_TIME)        
        self.assert_(dt < WAIT_TIME + 1)
    
    def test_unsubscribe_request_view(self):
        """ Test the unsubscribe request form. """
        r = self.client.get(self.unsubscribe_url)
        
        self.assertContains(r, self.n.title, status_code=200)
        self.assertContains(r, 'input id="id_email_field" type="text" name="email"')
        
        self.assertEqual(r.context['newsletter'], self.n)
    
    def test_unsubscribe_request_post(self):
        """ Post the unsubscribe request form. """
        subscription = Subscription(newsletter=self.n, name='Test Name', email='test@email.com', activated=True)
        subscription.save()
        
        r = self.client.post(self.unsubscribe_url, {'email_field':'test@email.com'})
        
        self.assertContains(r, self.n.title, status_code=200)
        self.assertNotContains(r, 'input id="id_email_field" type="text" name="email"')
        
        self.assertInContext(r, 'newsletter', Newsletter, self.n)
        self.assertInContext(r, 'form', UpdateRequestForm)
        
        self.assertEqual(subscription, r.context['form'].instance)
        
        """ Check the subscription email. """
        self.assertEquals(len(mail.outbox), 1)
                
        activate_url = subscription.unsubscribe_activate_url()
        full_activate_url = 'http://%s%s' % (self.site.domain, activate_url)
        
        self.assertEmailContains(full_activate_url)
    
    def test_unsubscribe_request_activate(self):
        """ Update a request. """
        subscription = Subscription(newsletter=self.n, name='Test Name', email='test@email.com')
        subscription.save()
        
        activate_url = subscription.unsubscribe_activate_url()
        
        r = self.client.get(activate_url)
        self.assertInContext(r, 'form', UpdateForm)
        self.assertContains(r, subscription.activation_code)
        
        testname2 = 'Test Name2'
        testemail2 = 'test2@email.com'
        r = self.client.post(activate_url, {'name_field':testname2, 'email_field':testemail2, 'user_activation_code':subscription.activation_code})        
        self.assertInContext(r, 'form', UpdateForm)
        
        subscription = getattr(r.context['form'], 'instance', None)
        self.assert_(subscription)
        self.assertEqual(subscription.name, testname2)
        self.assertEqual(subscription.email, testemail2)
    
    def test_unsubscribe_request_view(self):
        """ Test the unsubscribe request form. """
        r = self.client.get(self.unsubscribe_url)
        
        self.assertContains(r, self.n.title, status_code=200)
        self.assertContains(r, 'input id="id_email_field" type="text" name="email_field"')
        
        self.assertEqual(r.context['newsletter'], self.n)
    
    def test_unsubscribe_request_post(self):
        """ Post the unsubscribe request form. """
        subscription = Subscription(newsletter=self.n, name='Test Name', email='test@email.com', subscribed=True)
        subscription.save()
        
        r = self.client.post(self.unsubscribe_url, {'email_field':'test@email.com'})
        
        self.assertContains(r, self.n.title, status_code=200)
        self.assertNotContains(r, 'input id="id_email_field" type="text" name="email"')
        
        self.assertInContext(r, 'newsletter', Newsletter, self.n)
        self.assertInContext(r, 'form', UpdateRequestForm)
        
        self.assertEqual(subscription, r.context['form'].instance)
        
        """ Check the subscription email. """
        self.assertEquals(len(mail.outbox), 1)
                
        activate_url = subscription.unsubscribe_activate_url()
        full_activate_url = 'http://%s%s' % (self.site.domain, activate_url)
        
        self.assertEmailContains(full_activate_url)
    
    def test_unsubscribe_request_activate(self):
        """ Update a request. """
        subscription = Subscription(newsletter=self.n, name='Test Name', email='test@email.com')
        subscription.save()
        
        activate_url = subscription.unsubscribe_activate_url()
        
        r = self.client.get(activate_url)
        self.assertInContext(r, 'form', UpdateForm)
        self.assertContains(r, subscription.activation_code)
        
        testname2 = 'Test Name2'
        testemail2 = 'test2@email.com'
        r = self.client.post(activate_url, {'name_field':testname2, 'email_field':testemail2, 'user_activation_code':subscription.activation_code})        
        self.assertInContext(r, 'form', UpdateForm)
        
        subscription = getattr(r.context['form'], 'instance', None)
        self.assert_(subscription)
        self.assert_(subscription.unsubscribed)
        
        self.assert_((datetime.now() - subscription.unsubscribe_date).seconds < 2)
