app.controller("ServicesController", [
    "$scope",
    "$http",
    "$timeout",
    "$state",
    "$stateParams",
    "appService",
    "$interval",
    function ($scope, $http, $timeout, $state, $stateParams, appService, $interval) {

        $scope.resumes = []; // Initialize resumes array

        // Function to fetch services from the server
        $scope.fetchResumeFiles = function () {
            appService.fetchResumeFiles().then(function (data) {

              $scope.resumes = data; // Pass the data to the controller
              console.log($scope.resumes);

            }).catch(function (error) {
              alert(error.data);
            });
        };
    
        $scope.fetchResumeFiles();

        $scope.getThumbnail = function(resume) {
            return `/apiGetThumbnail/${resume.id}`;
        }

        $scope.select = function (resume) {
            $scope.selectedResume = resume; // Store the selected resume in the scope
            console.log("Selected resume:", resume); // Log the selected resume
        }
        
        $scope.callInsights = function (fileId) {
          fetch(`/apiGetJobs/${fileId}`)
            .then(function (response) {
              if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
              }
              return response.json(); // Parse the JSON from the response
            })
            .then(function (data) {
              console.log("Success");
            })
            .catch(function (error) {
              console.error(error);
            });
        }

        $scope.getIconSrc = function (fileType) {
          if (fileType.endsWith('pdf')) {
            return '/static/images/fileIcon/pdf.png';
          } else if (fileType.endsWith('jpeg') || fileType.endsWith('jpg')) {
            return '/static/images/fileIcon/img.png';
          } else if (fileType.endsWith('png')) {
            return '/static/images/fileIcon/img.png';
          }
          return 'https://cdn-icons-png.flaticon.com/512/833/833524.png'; // Default icon for unknown file types
        };

    }
    ]);