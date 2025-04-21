app.controller("CourseRecoController", [
  "$scope",
  "$http",
  "$timeout",
  "$state",
  "$stateParams",
  "appService",
  "$interval",
  function ($scope, $http, $timeout, $state, $stateParams, appService, $interval) {
    
    $scope.showForm = true;
    $scope.courseInput = {};

    $scope.getRecommendations = function () {

      console.log("Topic: " + $scope.courseInput.topic);
      console.log("Level: " + $scope.courseInput.level);

      $http.get(`/apiGetCourses/${$scope.courseInput.topic}/${$scope.courseInput.level}/  `, {
        headers: {
          'Content-Type': 'application/json'  // Specify the content type
        }
      }).then(function (response) {
        $scope.courses = response.data; // Assuming the backend returns an array of courses
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
