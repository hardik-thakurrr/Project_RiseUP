app.controller("JobRecoController", [
  "$scope",
  "$http",
  "$timeout",
  "$state",
  "$stateParams",
  "appService",
  "$interval",
  "resumeInsights",
  function ($scope, $http, $timeout, $state, $stateParams, appService, $interval, resumeInsights) {

    $scope.roles = resumeInsights.roles;
    $scope.showForm = true;
    $scope.id = $stateParams.resumeId;

    $scope.jobInput = {};

    $scope.jobInput.customRole = false;

    $scope.jobInput.customJobRole = "";
    $scope.jobInput.dropdownRole = "";

    $scope.getRecommendations = function () {

      if($scope.jobInput.customRole === true && $scope.jobInput.customJobRole != "") {
        $scope.jobInput.jobRole = $scope.jobInput.customJobRole;

      }else if($scope.jobInput.dropdownRole != "Other" && $scope.jobInput.dropdownRole != "") {
        $scope.jobInput.jobRole = $scope.jobInput.dropdownRole;
      } 
      else {
        $scope.errMessage = "Please select or enter a job role.";
        $scope.errTitle = "Missing Job Role";
        let toastEl = new bootstrap.Toast(document.getElementById("errToast"));
        toastEl.show();
        return;
      }


      $http.get(`/apiGetJobs/${$scope.id}/${$scope.jobInput.jobRole}/${$scope.jobInput.location}/  `, {
        headers: {
          'Content-Type': 'application/json'  // Specify the content type
        }
      }).then(function (response) {
        $scope.jobs = response.data; // Assuming the backend returns an array of courses
        $scope.showForm = false; // Hide the form after submission
      }).catch(function (error) {
        $scope.errTitle = "Failed!";
        $scope.errMessage = "Please try again later.";
        let toastEl = new bootstrap.Toast(document.getElementById("errToast"));
        toastEl.show();
      });
    };

  }
]);
