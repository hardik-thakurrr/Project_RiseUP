var app = angular.module('authApp', ["spinkitLoader"]);

app.controller('AuthController', ['$scope', '$http', '$httpParamSerializer', '$timeout', function ($scope, $http, $httpParamSerializer, $timeout) {
    $scope.showErrorModel = false;
    $scope.modalMessage = '';
    $scope.passwordFieldType = 'password';

    $scope.signUp = function () {
        $scope.showErrorModel = false;
        $scope.modalMessage = '';
        $scope.isEmailFocused = false;
        var flag = 0
        var username = $scope.username;
        var password = $scope.password;
        var email = $scope.email;
        var csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;
        var emailPattern = /^[\w\.-]+@[\w\.-]+\.\w+$/;
        var passwordPattern = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,}$/;
        var errors = [];
        if (username.length == 0) {
            flag = 1;
            errors.push('Enter a username');
        }
        if (!emailPattern.test(email)) {
            flag = 1;
            errors.push('Enter a valid email address');
        }
        if (!passwordPattern.test(password)) {
            flag = 1;
            errors.push('Password should be atleast 8 characters long and should contain both letters and special character');
        }
        if (errors.length > 0) {
            flag = 1
            $scope.modalMessage = errors.join('\n');
        }
        if (flag == 0) {
            var data = $httpParamSerializer({
                'username': $scope.username,
                'email': $scope.email,
                'password': $scope.password,
                'csrfmiddlewaretoken': csrf_token
            });
            $http.post('/apiSignup/', data,
                {
                    headers: {
                        'X-CSRFToken': csrf_token,
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                }
            ).then(function (response) {
                if (response.data.success) {
                    $scope.openToast("successToast", "Account Created", response.data.error);
                    document.getElementById('signupForm').reset();
                    document.getElementById('signIn').click();
                }
                else {
                    $scope.openToast("errToast", "Error in Creating Account", response.data.error);
                };
            }, function (error) {
                $scope.openToast("errToast", "Error in Creating Account", error.data);
            });


        }
    }

    $scope.signIn = function () {
        $scope.showErrorModel = false;
        $scope.isEmailFocused = false;
        $scope.isPasswordFocussed = false;
        var email = $scope.emailsignin;
        var password = $scope.passwordsignin;
        var csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;
        var flag = 0;
        var errors = [];
        if (email.length == 0) {
            flag = 1;
            errors.push('Email Id is required');
        }
        if (password.length == 0) {
            flag = 1;
            errors.push('Password is required')
        }
        if (errors.length > 0) {
            $scope.showErrorModel = true;
        }
        if (flag == 0) {

            var data = $httpParamSerializer({
                'email': email,
                'password': password,
                'csrfmiddlewaretoken': csrf_token
            });
            $http.post('/apiLogin/', data,
                {
                    headers: {
                        'X-CSRFToken': csrf_token,
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                }
            ).then(function (response) {
                if (response.data.success) {
                    window.location.href = "/resumes";
                }
                else {
                    $scope.openToast("errToast", "Invalid Credentials", response.data.error);
                }
            }, function (error) {
                $scope.openToast("errToast", "Login Failed", "Please try Again");
                alert('An unexpected error occurred: ' + error.data);
                console.error(error);
            });
        }
    }

    $scope.togglePasswordVisibility = function () {
        $scope.passwordFieldType = ($scope.passwordFieldType == 'password') ? 'text' : 'password';
    };

    $scope.openToast = function (toastType, heading, error) {

        var myToastEl = document.getElementById(toastType)
        var myToast = new bootstrap.Toast(myToastEl, {
            delay: 5000
        });
        $scope.errTitle = heading;
        $scope.errMessage = error;
        myToast.show();

    };

    $scope.closeErrorModal = function () {
        $scope.showErrorModal = false;
    };


}])