app.controller("ResumeController", [
  "$scope",
  "$http",
  "$timeout",
  "$state",
  "$stateParams",
  "appService",
  "resumeFileList",
  "$interval",
  function ($scope, $http, $timeout, $state, $stateParams, appService, resumeFileList, $interval) {
    $scope.files = resumeFileList;
    $scope.actionForFile = null;
    $scope.searchText = '';
    $scope.possibleFYs = []; // Array to hold possible FYs  
    $scope.isLoading = false;
    $scope.allFiles = { selected: false };
    $scope.modelName = "";

    $scope.initializeTooltips = function () {
      // Wait for DOM rendering
      setTimeout(function () {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
          return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
          });
        });
      }, 500);
    };

    $scope.fetchProjectDetails = function () {
      fetch(`/apiFetchResumes/`)
        .then(function (response) {
          if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
          }
          return response.json(); // Parse the JSON from the response
        })
        .then(function (data) {
          if (data) {
            data.forEach(function (newFile) {
              // Find files in $scope.files where fileStatus is "Processing" and update only those
              const existingFile = $scope.files.find(function (file) {
                return file.id === newFile.id && file.fileStatus === "Processing";
              });

              if (existingFile) {
                // Update the file object with the new data
                angular.extend(existingFile, newFile);
              }
            });
            $scope.$apply(); // Manually trigger a digest cycle to update the view
          }
        })
        .catch(function (error) {
          console.error(error);
        });
    }

    // Function to check if any file has status 'processing'
    $scope.hasProcessingFiles = function () {
      return $scope.files && $scope.files.some(file => file.fileStatus == "Processing");
    }

    // Set up polling every 5 seconds (5000 milliseconds)
    var intervalPromise = $interval(function () {
      if ($scope.hasProcessingFiles()) {
        $scope.fetchProjectDetails();
      }
    }, 5000);

    // Clean up the interval when the controller is destroyed
    $scope.$on("$destroy", function () {
      $interval.cancel(intervalPromise);
    });

    // Call the tooltip initialization function when the view is loaded
    $scope.$on('$viewContentLoaded', function () {
      $scope.initializeTooltips();
    });

    $scope.toggleSelectAll = function () {
      const filteredFiles = $scope.files.filter($scope.startsWithFilter);
      angular.forEach(filteredFiles, function (file) {
        file.selected = $scope.allFiles.selected;
      });
    };

    $scope.toggleFileSelection = function(file) {
      if(file.fileStatus != 'Processing') {
        file.selected = !file.selected;
      }
    }

    $scope.allChecked = function () {
      // Automatically check/uncheck 'Select All' checkbox based on filtered files
      const filteredFiles = $scope.files.filter($scope.startsWithFilter);
      return filteredFiles.every(file => file.selected);
    };

    $scope.getSelectedFiles = function () {
      let selectedFiles = $scope.files.filter(file => $scope.startsWithFilter(file) && file.selected);
      return selectedFiles;
    };

    $scope.getTaggedSelectedFiles = function() {
      return $scope.getSelectedFiles().filter(file => file.fileStatus === "Tagged");
    };

    $scope.$watch("files", function (newVal) {
      if (newVal != null) {
        $scope.allFiles.selected = $scope.allChecked();
      }
    }, true);

    // Watch for changes in the searchText to trigger updateFilteredFiles
    $scope.$watch('searchText', function (newVal, oldVal) {
      if (newVal !== oldVal) {
        $scope.allFiles.selected = $scope.allChecked();
      }
    });

    // Initialize status based on $stateParams
    const statusString = $stateParams.status;

    // Create an empty status object
    $scope.status = {};

    // If statusString exists, split it and set the corresponding keys to true
    if (statusString) {
      let statusArray = statusString.split(','); // Split the comma-separated string
      statusArray.forEach(statusKey => {
        $scope.status[statusKey] = true; // Set the status key to true
      });
    }

    // Initialize other search parameters from $stateParams
    $scope.fromDate = $stateParams.fromDate ? new Date($stateParams.fromDate) : null;
    $scope.toDate = $stateParams.toDate ? new Date($stateParams.toDate) : null;
    $scope.fyFilter = $stateParams.fyFilter || null;

    $scope.handleSearch = function () {
      // Convert status object to a comma-separated string of true keys
      let statusArray = Object.keys($scope.status || {})
        .filter(key => $scope.status[key] === true);

      let searchParams = {
        fromDate: $scope.fromDate ? new Date($scope.fromDate).toISOString() : null,
        toDate: $scope.toDate ? new Date($scope.fromDate).toISOString() : null,
        fyFilter: $scope.fyFilter,
        status: statusArray.length > 0 ? statusArray.join(',') : null  // Join true values with commas
      };

      // Filter out null, undefined, or empty values
      const filteredSearchParams = Object.keys(searchParams)
        .filter(key => searchParams[key] !== null && searchParams[key] !== undefined && searchParams[key] !== '')
        .reduce((acc, key) => {
          acc[key] = searchParams[key];
          return acc;
        }, {});

      // Build the query parameters for the URL
      const params = new URLSearchParams(filteredSearchParams).toString();

      // Send the request using fetch
      fetch(`/apiFetchResumes/?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      })
        .then(response => response.json())  // Parse the JSON response
        .then(data => {
          $scope.files.splice(0, $scope.files.length, ...data);
          $scope.$apply();

          // Update the state with query parameters, excluding any null or undefined ones
          $state.go('resumes', searchParams, { notify: false });
        })
        .catch(error => {
          console.error('Error fetching filtered files:', error);
        });
    }

    $scope.clearFilter = function (filterType) {
      if (filterType === 'fromDate') {
        $scope.fromDate = null;
      } else if (filterType === 'toDate') {
        $scope.toDate = null;
      } else if (filterType === 'fyFilter') {
        $scope.fyFilter = null;
      } else if (filterType === 'status') {
        $scope.status = {
          'Processing': false,
          'Un-Tagged': false,
          'Tagged': false,
          'Validated': false
        };
      }
      // Call the search function to reapply the filters
      $scope.handleSearch();
    };

    $scope.clearAllFilters = function () {
      $scope.fromDate = null;
      $scope.toDate = null;
      $scope.fyFilter = null;
      $scope.status = {
        'Processing': false,
        'Un-Tagged': false,
        'Tagged': false,
        'Validated': false
      };
      // Hide the tooltip manually after clearing the filters
      var clearBtn = document.querySelector('#clearAllFilters');
      var tooltipInstance = bootstrap.Tooltip.getInstance(clearBtn);
      if (tooltipInstance) {
        tooltipInstance.dispose(); // Dispose of the tooltip instance
      }
      // Reapply filters
      // $scope.handleSearch();
    };

    // WatchGroup for 'fromDate', 'toDate', and 'fyFilter'
    $scope.$watchGroup(['fromDate', 'toDate', 'fyFilter'], function (newValues) {

      if (!newValues.every(value => value === null)) {
        $scope.handleSearch(); // Call the common search handler function
      }
    });

    // Separate deep watch for 'status'
    $scope.$watch('status', function (newStatus) {

      $scope.handleSearch(); // Call the common search handler function
    }, true); // 'true' enables deep watching on the status object

    $scope.confirmDelete = function (fileId) {
      $http.delete('/apiDeleteFile/' + fileId)
        .then(function (response) {
          $scope.files = $scope.files.filter(file => file.id !== fileId);
          $scope.openToast("successToast", response.data);
        })
        .catch(function (error) {
          $scope.openToast("errToast", error.data);
        });
    };

    $scope.startsWithFilter = function (file) {
      if (!$scope.searchText) {
        return true;
      }
      return file.filename.toLowerCase().startsWith($scope.searchText.toLowerCase());
    };

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

    $scope.retryUpload = function (fileId, event) {
      event.target.firstElementChild.classList.add('fa-spin');

      // Use fetch to send the POST request
      fetch('/apiRetryUpload/' + fileId, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        }
      })
        .then(function (response) {
          if (!response.ok) {
            return response.json().then(err => { throw err; });
          }
          return response.json();
        })
        .then(function (data) {
          // Stop the button's spinner
          event.target.firstElementChild.classList.remove('fa-spin');

          // Update the file's status in the UI
          var fileIndex = $scope.files.findIndex(file => file.id === fileId);
          $scope.files[fileIndex].fileStatus = data;

          // Show success toast message
          $scope.openToast("successToast", data);
        })
        .catch(function (error) {
          // Stop the button's spinner even in case of error
          event.target.firstElementChild.classList.remove('fa-spin');

          // Show error toast message
          $scope.openToast("errToast", error);
        });
    }

    $scope.deleteSelectedFiles = function () {

      let selectedFiles = $scope.getSelectedFiles();

      if (selectedFiles.length === 0) {
        const err = {
          "title": "Invalid Operation",
          "message": "No files selected for Deletion"
        };
        $scope.openToast("errToast", err);
        return;
      }

      // Create an array of promises for each file deletion
      const deletePromises = selectedFiles.map(selectedFile => {
        const fileId = selectedFile.id; // Accessing the ID from the selected file

        return $http.delete('/apiDeleteFile/' + fileId)
          .then(response => {
            // Remove the file from the list after successful deletion
            $scope.files = $scope.files.filter(file => file.id !== fileId);
            return response.data; // Return response data for final toast
          })
          .catch(error => {
            // Handle individual error, but do not break the deletion process
            return Promise.reject(error.data);
          });
      });

      Promise.all(deletePromises)
        .then(responses => {
          const success = {
            "title": "Deleted Successfully",
            "message": "All selected files were Deleted"
          };
          $scope.openToast("successToast", success);
        })
        .catch(error => {
          const err = {
            "title": "Please try again",
            "message": "Error in deleting files"
          };
          $scope.openToast("errToast", err);
        });
    };

  
    $scope.setFileOfAction = function(file) {
      $scope.actionForFile=file;
    };

    $scope.confirmDelete = function (fileId) {
      $http.delete('/apiDeleteFile/' + fileId)
        .then(function (response) {
          $scope.files = $scope.files.filter(file => file.id !== fileId);
          $scope.openToast("successToast", response.data);
        })
        .catch(function (error) {
          $scope.openToast("errToast", error.data);
        });
    };

    $scope.openToast = function (toastType, error) {

      var myToastEl = document.getElementById(toastType)
      var myToast = new bootstrap.Toast(myToastEl, {
        delay: 5000
      });
      $scope.errTitle = error.title;
      $scope.errMessage = error.message;
      if (!$scope.$$phase && !$scope.$root.$$phase) {
        $scope.$apply();
      }
      myToast.show();

    };

    $scope.goToUploads = function () {
      $state.go("upload", {}, {reload: true})
    };

  }
]);
