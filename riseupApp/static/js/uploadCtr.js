app.directive('ngFileChange', function () {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {

            element.bind('change', function (event) {
                scope.$apply(function () {
                    scope[attrs.ngFileChange](event.target.files);
                });
            });
        }
    };
});

app.directive('ngDragOver', function () {
    return {
        restrict: 'A',
        link: function (scope, element) {
            element.bind('dragover', function (event) {
                event.preventDefault();
                element.addClass('dragover');
            });

            element.bind('dragleave', function () {
                element.removeClass('dragover');
            });

            element.bind('drop', function (event) {
                event.preventDefault();
                element.removeClass('dragover');
                scope.$apply(function () {
                    scope.updateFileInput(event.dataTransfer.files);
                });
            });
        }
    };
});

app.controller('UploadController', ['$scope', '$state', '$stateParams', '$http', 'appService', function ($scope, $state, $stateParams, $http, appService) {
    $scope.files = [];
    $scope.fileUrls = [];
    $scope.activeIndex = 0;
    $scope.progressVisible = false;
    $scope.isImageVisible = false;
    $scope.zoomLevel = 1.0;

    // Function to handle files
    $scope.handleFiles = function (files) {
        $scope.files = [...files];
        if (files.length > 0) {

            for (let index = 0; index < files.length; index++) {
                const file = files[index];

                // let type = file.name.split('.').pop().toLowerCase();
                let url = URL.createObjectURL(file);

                $scope.fileUrls.push(url);
            }

            var output = document.getElementById('output');
            output.onload = function () {
                URL.revokeObjectURL(output.data) // free memory
            }
        }
    };

    // Function to update the file input
    $scope.updateFileInput = function (files) {
        document.getElementById('fileInput').files = files;
        $scope.handleFiles(files);
    };

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

    $scope.uploadFile = function () {
        $scope.progressVisible = true;

        const formData = new FormData();
        angular.forEach($scope.files, function (file) {
            formData.append('file', file);
        });

        $http.post(`/apiUpload`, formData, {
            headers: {
                'Content-Type': undefined,
            },
            transformRequest: angular.identity
        }).then(function (response) {
            $scope.progressVisible = false;
            $scope.goToResumes();
        }).catch(function (error) {
            $scope.progressVisible = false;
            console.error(error);
            alert("Something went wrong. Please try again.");
        });
    };

    $scope.goToResumes = function () {
        $state.go("resumes", {}, { reload: true });
    };

    function updateZoom() {
        const viewer = document.getElementById('output');
        viewer.style.transform = `scale(${$scope.zoomLevel})`;
        viewer.style.transformOrigin = 'top left';
    }

    $scope.removeFile = function (index) {
        if (index == $scope.files.length - 1) {
            $scope.activeIndex--;
        }

        $scope.files.splice(index, 1);
        $scope.fileUrls.splice(index, 1);
    }

    $scope.changeSelection = function (event, index) {
        let currElement = event.currentTarget;
        currElement.classList.toggle('currentFile');
        $scope.activeIndex = index;
    }

    $scope.$watch('activeIndex', function (newIndex, oldIndex) {
        if ($scope.files.length > 0) {
            let filename = $scope.files[newIndex].name;
            $scope.isImageVisible = filename.slice(filename.lastIndexOf(".") + 1) != "pdf";
        }
    });

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

}]);
