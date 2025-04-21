(function() {
    'use strict';
    
    // Initialize the angular application
    angular
        .module('riseUpApp', [])
        .controller('MainController', MainController);
    
    // Inject dependencies
    MainController.$inject = ['$scope', '$window', '$location', '$anchorScroll'];
    
    function MainController($scope, $window, $location, $anchorScroll) {
        var vm = this;
        
        // View model properties
        vm.title = 'RiseUP - Your Personalized Career Companion';
        vm.isScrolled = false;
        vm.currentYear = new Date().getFullYear();
        vm.formData = {
            name: '',
            email: '',
            subject: '',
            message: ''
        };
        vm.formSubmitted = false;
        
        // Services and features data
        vm.services = [
            {
                title: 'Domain Expertise Prediction',
                description: 'Get matched to the right career fields based on your strengths and past experience.',
                icon: 'fa-chart-line'
            },
            {
                title: 'Personality Insights',
                description: 'Discover how your resume reflects your personality traits and soft skills.',
                icon: 'fa-user-graduate'
            },
            {
                title: 'Interactive Interview Bot',
                description: 'Practice with an AI-powered bot that asks tailored, domain-specific questions.',
                icon: 'fa-robot'
            },
            {
                title: 'Smart Resume Analysis',
                description: 'Receive detailed feedback on your resume\'s strengths, gaps, and how to improve it.',
                icon: 'fa-file-alt'
            },
            {
                title: 'Intelligent Question Generation',
                description: 'Get custom-generated interview questions based on your resume and targeted role.',
                icon: 'fa-question-circle'
            },
            {
                title: 'Speech and Behavior Feedback',
                description: 'Improve your communication with real-time speech-to-text conversion and behavioral tips.',
                icon: 'fa-comments'
            },
            {
                title: 'Personalized Job Recommendations',
                description: 'Discover job roles that match your skills, interests, and predicted domain.',
                icon: 'fa-briefcase'
            },
            {
                title: 'Tailored Course Suggestions',
                description: 'Get course recommendations that can boost your career prospects and fill skill gaps.',
                icon: 'fa-graduation-cap'
            }
        ];
        
        vm.features = [
            {
                title: 'Improve Your Resume',
                description: 'Get detailed insights and suggestions to make your resume stand out.',
                icon: 'fa-file-alt'
            },
            {
                title: 'Prepare for Interviews',
                description: 'Practice with an interactive interview bot that asks personalized questions and gives feedback.',
                icon: 'fa-comments'
            },
            {
                title: 'Generate Cover Letters',
                description: 'No more staring at a blank screen—just enter your resume and job role for instant letters.',
                icon: 'fa-envelope'
            },
            {
                title: 'Discover Career Paths',
                description: 'Receive tailored job and course recommendations based on your skills and interests.',
                icon: 'fa-road'
            }
        ];
        
        // Methods
        vm.scrollTo = scrollTo;
        vm.scrollToTop = scrollToTop;
        vm.submitForm = submitForm;
        vm.resetForm = resetForm;
        
        // Initialize controller
        activate();
        
        ////////////////
        
        function activate() {
            // Initialize any features or data needed on page load
            console.log('MainController activated');
            
            // Initialize AOS animation library
            AOS.init({
                duration: 800,
                once: true,
                offset: 100
            });
            
            // Handle scroll events
            $window.addEventListener('scroll', checkScroll);
            
            // Function to check if page is scrolled
            function checkScroll() {
                var scrollPosition = $window.pageYOffset;
                vm.isScrolled = scrollPosition > 50;
                $scope.$apply();
            }
        }
        
        // Function to handle smooth scrolling to sections
        function scrollTo(elementId) {
            $location.hash(elementId);
            $anchorScroll();
            closeMenu();
        }
        
        // Function to scroll back to top
        function scrollToTop() {
            $window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        // Function to close mobile menu after click
        function closeMenu() {
            var navbarCollapse = document.getElementById('navbarNav');
            if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                var bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.hide();
            }
        }
        
        // Function to handle form submission
        function submitForm() {
            // In a real application, you would send the form data to a server
            console.log('Form submitted:', vm.formData);
            vm.formSubmitted = true;
            
            // For demo purposes, just reset the form after 3 seconds
            $window.setTimeout(function() {
                resetForm();
                $scope.$apply();
            }, 3000);
        }
        
        // Function to reset the form
        function resetForm() {
            vm.formData = {
                name: '',
                email: '',
                subject: '',
                message: ''
            };
            vm.formSubmitted = false;
            
            if ($scope.contactForm) {
                $scope.contactForm.$setPristine();
                $scope.contactForm.$setUntouched();
            }
        }
    }
})();