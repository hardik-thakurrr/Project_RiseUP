// app.js
var app = angular.module("fileUploadApp", ["ui.router", "spinkitLoader"]);

app.config([
  "$stateProvider",
  "$urlRouterProvider",
  "$urlMatcherFactoryProvider",
  "$locationProvider",
  "$sceProvider",
  function (
    $stateProvider,
    $urlRouterProvider,
    $urlMatcherFactoryProvider,
    $locationProvider,
    $sceProvider
  ) {
    $sceProvider.enabled(false);

    $urlMatcherFactoryProvider.strictMode(false);

    $urlRouterProvider.otherwise("/resumes");

    $stateProvider
      .state("upload", {
        url: "/upload",
        templateUrl: "/index/upload/",
        controller: "UploadController"
      })
      .state("resumes", {
        url: "/resumes?fromDate&toDate&fyFilter&status",
        templateUrl: "/index/resumes/",
        controller: "ResumeController",
        params: {
          fromDate: { value: null, squash: true },
          toDate: { value: null, squash: true },
          fyFilter: { value: null, squash: true },
          status: { value: null, squash: true }
        },
        resolve: {
          resumeFileList: function (appService, $stateParams) {
            return appService.fetchResumeFiles().then(function (data) {

              return data; // Pass the data to the controller

            }).catch(function (error) {
              alert(error.data);
              return $q.reject(error); // Prevent controller from initializing
            });
          }
        }
      })
      .state("services", {
        url: "/services",
        templateUrl: "/index/services/",
        controller: "ServicesController"
      })
      .state("resumeInsights", {
        url: "/resumeInsights/:resumeId",
        params: {
          resumeId: null,
        },
        templateUrl: "/index/resumeInsights/",
        controller: "ResumeInsightsController",
        resolve: {
          resumeInsights: function (appService, $stateParams) {
            return appService.fetchResumeInsights($stateParams.resumeId).then(function (data) {

              return data; // Pass the data to the controller

            }).catch(function (error) {
              alert(error.data);
              return $q.reject(error); // Prevent controller from initializing
            });
          }
        }
      })
      .state("jobRoles", {
        url: "/jobRoles/:resumeId",
        params: {
          resumeId: null,
        },
        templateUrl: "/index/jobRoles/",
        controller: "JobRolesController",
        resolve: {
          jobRoles: function (appService, $stateParams) {
            return appService.fetchResumeInsights($stateParams.resumeId).then(function (data) {

              let {domain, roles, ...others} = data;
              return {domain, roles}; // Pass the data to the controller

            }).catch(function (error) {
              alert(error.data);
              return $q.reject(error); // Prevent controller from initializing
            });
          }
        }
      })
      .state("personality", {
        url: "/personality",
        templateUrl: "/index/personality/",
        controller: "PersonalityController"
      })
      .state("interviewBot", {
        url: "/interviewBot/:resumeId",
        params: {
          resumeId: null,
        },
        templateUrl: "/index/interviewBot/",
        controller: "InterviewBotController"
      })
      .state("jobReco", {
        url: "/jobRecommendations/:resumeId",
        params: {
          resumeId: null,
        },
        templateUrl: "/index/jobReco/",
        controller: "JobRecoController",
        resolve: {
          resumeInsights: function (appService, $stateParams) {
            return appService.fetchResumeInsights($stateParams.resumeId).then(function (data) {

              return data; // Pass the data to the controller

            }).catch(function (error) {
              alert(error.data);
              return $q.reject(error); // Prevent controller from initializing
            });
          }
        }
      })
      .state("courseReco", {
        url: "/courseRecommendations",
        templateUrl: "/index/courseReco/",
        controller: "CourseRecoController"
      })
      .state("coverLetter", {
        url: "/coverLetter/:resumeId",
        params: {
          resumeId: null,
        },
        templateUrl: "/index/coverLetter/",
        controller: "CoverLetterController",
        resolve: {
          coverLetter: function (appService, $stateParams) {
            return appService.fetchCoverLetter($stateParams.resumeId).then(function (data) {

              return data; // Pass the data to the controller

            }).catch(function (error) {
              alert(error.data);
              return $q.reject(error); // Prevent controller from initializing
            });
          }
        }
      })
      .state("profile", {
        url: "/profile",
        templateUrl: "/index/profile/",
        controller: "ProfileController",
        resolve: {
          userProfile: function (appService) {
            return appService.fetchProjectDetails().then(function (data) {

              return data; // Pass the data to the controller

            }).catch(function (error) {
              alert(error.data);
              return $q.reject(error); // Prevent controller from initializing
            });
          }
        }
      });

    $locationProvider.html5Mode(true);
  },
]);
