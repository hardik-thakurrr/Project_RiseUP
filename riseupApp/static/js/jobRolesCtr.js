app.controller("JobRolesController", [
  "$scope",
  "$http",
  "$timeout",
  "$state",
  "$stateParams",
  "appService",
  "$interval",
  "jobRoles",
  function ($scope, $http, $timeout, $state, $stateParams, appService, $interval, jobRoles) {

    $scope.jobRoles = jobRoles;
    
    console.log("JobRolesController initialized with jobRoles:", jobRoles);

  }
]);
