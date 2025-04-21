app.controller("ResumeInsightsController", [
  "$scope",
  "$http",
  "$timeout",
  "$state",
  "$stateParams",
  "appService",
  "$interval",
  "resumeInsights",
  function ($scope, $http, $timeout, $state, $stateParams, appService, $interval, resumeInsights) {
    
    $scope.resumeInsights = resumeInsights;
    $scope.resumeId = $stateParams.resumeId;

    console.log("Resume Insights Data:", resumeInsights);

  }
]);
