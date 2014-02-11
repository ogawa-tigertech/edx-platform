# -*- coding: utf-8 -*-
"""
E2E tests for the LMS.
"""

from unittest import skip

from bok_choy.web_app_test import WebAppTest
from bok_choy.promise import EmptyPromise, fulfill_before

from .helpers import UniqueCourseTest, load_data_str
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.lms.login import LoginPage
from ..pages.lms.find_courses import FindCoursesPage
from ..pages.lms.course_about import CourseAboutPage
from ..pages.lms.register import RegisterPage
from ..pages.lms.course_info import CourseInfoPage
from ..pages.lms.tab_nav import TabNavPage
from ..pages.lms.course_nav import CourseNavPage
from ..pages.lms.progress import ProgressPage
from ..pages.lms.dashboard import DashboardPage
from ..pages.lms.video import VideoPage
from ..fixtures.course import CourseFixture, XBlockFixtureDesc, CourseUpdateDesc


class RegistrationTest(UniqueCourseTest):
    """
    Test the registration process.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(RegistrationTest, self).setUp()

        self.find_courses_page = FindCoursesPage(self.browser)
        self.course_about_page = CourseAboutPage(self.browser, self.course_id)

        # Create a course to register for
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        ).install()

    def test_register(self):

        # Visit the main page with the list of courses
        self.find_courses_page.visit()

        # Expect that the fixture course exists
        course_ids = self.find_courses_page.course_id_list
        self.assertIn(self.course_id, course_ids)

        # Go to the course about page and click the register button
        self.course_about_page.visit()
        register_page = self.course_about_page.register()

        # Fill in registration info and submit
        username = "test_" + self.unique_id[0:6]
        register_page.provide_info(
            username + "@example.com", "test", username, "Test User"
        )
        dashboard = register_page.submit()

        # We should end up at the dashboard
        # Check that we're registered for the course
        course_names = dashboard.available_courses
        self.assertIn(self.course_info['display_name'], course_names)


class LanguageTest(UniqueCourseTest):
    """
    Tests that the change language functionality on the dashboard works
    """

    def setUp(self):
        """
        Initiailize dashboard page
        """
        super(LanguageTest, self).setUp()
        self.dashboard_page = DashboardPage(self.browser)

    def test_change_lang(self):
        AutoAuthPage(self.browser, course_id=self.course_id).visit()
        self.dashboard_page.visit()
        # Change language to Dummy Esperanto
        self.dashboard_page.change_language("eo")

        # This string is unicode for "ÇÜRRÉNT ÇØÜRSÉS", which should appear in our Dummy Esperanto page
        seektext = u"\xc7\xdcRR\xc9NT \xc7\xd8\xdcRS\xc9S"
        self.browser.is_text_present(seektext)
        self.assertTrue(self.browser.is_text_present(seektext))

    def test_language_persists(self):
        auto_auth_page = AutoAuthPage(self.browser, course_id=self.course_id)
        auto_auth_page.visit()

        self.dashboard_page.visit()
        # Change language to Dummy Esperanto
        self.dashboard_page.change_language("eo")

        # destroy session
        self.browser._cookie_manager.delete()

        # log back in
        auto_auth_page.visit()

        self.dashboard_page.visit()
        # This string is unicode for "ÇÜRRÉNT ÇØÜRSÉS", which should appear in our Dummy Esperanto page
        seektext = u"\xc7\xdcRR\xc9NT \xc7\xd8\xdcRS\xc9S"
        self.browser.is_text_present(seektext)
        self.assertTrue(self.browser.is_text_present(seektext))


class HighLevelTabTest(UniqueCourseTest):
    """
    Tests that verify each of the high-level tabs available within a course.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(HighLevelTabTest, self).setUp()

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.progress_page = ProgressPage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
        self.tab_nav = TabNavPage(self.browser)
        self.video = VideoPage(self.browser)

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_update(
            CourseUpdateDesc(date='January 29, 2014', content='Test course update')
        )

        course_fix.add_handout('demoPDF.pdf')

        course_fix.add_children(
            XBlockFixtureDesc('static_tab', 'Test Static Tab'),
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Problem 1', data=load_data_str('multiple_choice.xml')),
                    XBlockFixtureDesc('problem', 'Test Problem 2', data=load_data_str('formula_problem.xml')),
                    XBlockFixtureDesc('html', 'Test HTML'),
            )),
            XBlockFixtureDesc('chapter', 'Test Section 2').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection 2'),
                XBlockFixtureDesc('sequential', 'Test Subsection 3'),
        )).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    def test_course_info(self):
        """
        Navigate to the course info page.
        """
        # Navigate to the course info page from the progress page
        self.progress_page.visit()
        self.tab_nav.go_to_tab('Course Info')

        # Expect just one update
        self.assertEqual(self.course_info_page.num_updates, 1)

        # Expect a link to the demo handout pdf
        handout_links = self.course_info_page.handout_links
        self.assertEqual(len(handout_links), 1)
        self.assertIn('demoPDF.pdf', handout_links[0])

    def test_progress(self):
        """
        Navigate to the progress page.
        """
        # Navigate to the progress page from the info page
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Progress')

        # We haven't answered any problems yet, so assume scores are zero
        # Only problems should have scores; so there should be 2 scores.
        CHAPTER = 'Test Section'
        SECTION = 'Test Subsection'
        EXPECTED_SCORES = [(0, 3), (0, 1)]

        actual_scores = self.progress_page.scores(CHAPTER, SECTION)
        self.assertEqual(actual_scores, EXPECTED_SCORES)

    def test_static_tab(self):
        """
        Navigate to a static tab (course content)
        """
        # From the course info page, navigate to the static tab
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Test Static Tab')
        self.assertTrue(self.tab_nav.is_on_tab('Test Static Tab'))

    def test_courseware_nav(self):
        """
        Navigate to a particular unit in the courseware.
        """
        # Navigate to the courseware page from the info page
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Courseware')

        # Check that the courseware navigation appears correctly
        EXPECTED_SECTIONS = {
            'Test Section': ['Test Subsection'],
            'Test Section 2': ['Test Subsection 2', 'Test Subsection 3']
        }
        actual_sections = self.course_nav.sections
        for section, subsections in EXPECTED_SECTIONS.iteritems():
            self.assertIn(section, actual_sections)
            self.assertEqual(actual_sections[section], EXPECTED_SECTIONS[section])

        # Navigate to a particular section
        self.course_nav.go_to_section('Test Section', 'Test Subsection')

        # Check the sequence items
        EXPECTED_ITEMS = ['Test Problem 1', 'Test Problem 2', 'Test HTML']

        actual_items = self.course_nav.sequence_items
        self.assertEqual(len(actual_items), len(EXPECTED_ITEMS))
        for expected in EXPECTED_ITEMS:
            self.assertIn(expected, actual_items)


class VideoTest(UniqueCourseTest):
    """
    Navigate to a video in the courseware and play it.
    """
    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(VideoTest, self).setUp()

        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)
        self.tab_nav = TabNavPage(self.browser)
        self.video = VideoPage(self.browser)

        # Install a course fixture with a video component
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('video', 'Video')
        ))).install()


        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()

    @skip("BLD-563: Video Player Stuck on Pause")
    def test_video_player(self):
        """
        Play a video in the courseware.
        """

        # Navigate to a video
        self.course_info_page.visit()
        self.tab_nav.go_to_tab('Courseware')

        # The video should start off paused
        # Since the video hasn't loaded yet, it's elapsed time is 0
        self.assertFalse(self.video.is_playing)
        self.assertEqual(self.video.elapsed_time, 0)

        # Play the video
        self.video.play()

        # Now we should be playing
        self.assertTrue(self.video.is_playing)

        # Wait for the video to load the duration
        video_duration_loaded = EmptyPromise(
            lambda: self.video.duration > 0,
            'video has duration', timeout=20
        )

        with fulfill_before(video_duration_loaded):

            # Pause the video
            self.video.pause()

            # Expect that the elapsed time and duration are reasonable
            # Again, we can't expect the video to actually play because of
            # latency through the ssh tunnel
            self.assertGreaterEqual(self.video.elapsed_time, 0)
            self.assertGreaterEqual(self.video.duration, self.video.elapsed_time)
