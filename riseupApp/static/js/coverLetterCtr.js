app.controller("CoverLetterController", [
  "$scope",
  "$http",
  "$timeout",
  "$state",
  "$stateParams",
  "appService",
  "$interval",
  "coverLetter",
  function ($scope, $http, $timeout, $state, $stateParams, appService, $interval, coverLetter) {

    $scope.zoomLevel = 1;
    
    $scope.coverLetter = coverLetter.trimStart();

    $scope.zoomIn = function () {
      $scope.zoomLevel += 0.1;
      updateZoom();
    };

    $scope.zoomOut = function () {
      if ($scope.zoomLevel > 1) {
          $scope.zoomLevel -= 0.1;
          updateZoom();
      }
    };

    function updateZoom() {
      const viewer = document.getElementById('output');
      viewer.style.transform = `scale(${$scope.zoomLevel})`;
      viewer.style.transformOrigin = 'top left';
    }

    // Load the original uploaded file (pdf or image)
    $scope.loadUploadedFile = function () {
      $http({
        method: 'GET',
        url: `/apiGetCoverFile/${$stateParams.resumeId}`,
        responseType: 'blob'
      }).then(function (response) {
        const contentType = response.headers('Content-Type');
        const blob = new Blob([response.data], { type: contentType });
        const fileURL = URL.createObjectURL(blob);

        if (contentType === 'application/pdf') {
          $scope.uploadedFileType = 'pdf';
        } else if (contentType.startsWith('image/')) {
          $scope.uploadedFileType = 'image';
        } else {
          console.warn('Unsupported content type:', contentType);
          $scope.uploadedFileType = null;
        }

        $scope.uploadedFileUrl = fileURL;
      }, function (error) {
        console.error("Error fetching uploaded file:", error);
      });
    };

    // Initial load
    $scope.loadUploadedFile();
  }
]);
