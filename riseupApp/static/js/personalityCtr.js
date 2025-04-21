app.controller("PersonalityController", [
  "$scope",
  "$http",
  "$timeout",
  "$state",
  "$stateParams",
  "appService",
  "$interval",
  function ($scope, $http, $timeout, $state, $stateParams, appService, $interval) {
    
    $scope.userInput = {};
    $scope.traitOrder = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"];
    $scope.currentIndex = 0;
    $scope.currentTrait = $scope.traitOrder[$scope.currentIndex];
    $scope.showForm = true;

    $scope.traitTitles = {
      openness: "I enjoy trying new things and exploring new ideas",
      conscientiousness: "I am organized and like to plan ahead",
      extraversion: "I am a confident and assertive leader",
      agreeableness: "I seek harmony and cooperation in relationships",
      neuroticism: "I often feel anxious or emotionally reactive"
    };

    $scope.traitDescriptions = {
      openness: "I am eager to try new experiences, value creative expression, and enjoy exploring diverse ideas, art, and cultures.",
      conscientiousness: "I pride myself on being organized, reliable, and goal-oriented, consistently planning ahead and maintaining high standards in all aspects of my life.",
      extraversion: "I feel energized by social interactions, enjoy initiating conversations, and am comfortable taking a leading role in group settings.",
      agreeableness: "I value harmonious relationships, am empathetic and cooperative, and often go out of my way to help others while avoiding conflicts.",
      neuroticism: "I frequently experience intense emotions such as anxiety or mood fluctuations, and sometimes find it challenging to remain calm under pressure."
    };

    $scope.progressPercentage = function () {
      return Math.round(($scope.currentIndex / $scope.traitOrder.length) * 100);
    };

    $scope.isLastTrait = function () {
      return $scope.currentIndex === $scope.traitOrder.length - 1;
    };

    $scope.nextTrait = function () {
      const next = () => {
        if ($scope.isLastTrait()) {
          $scope.submitPersonality();
        } else {
          $scope.currentIndex++;
          $scope.currentTrait = $scope.traitOrder[$scope.currentIndex];
        }
      };

      // Add swipe animation
      const el = document.querySelector('.fade-slide');
      el.classList.remove('show');
      setTimeout(() => {
        $scope.$apply(next);
        el.classList.add('show');
      }, 300);
    };

    $scope.submitPersonality = function () {
      console.log("Final User Input:", $scope.userInput);

      // Send user input to the backend
      const formData = {
        userInput: $scope.userInput
      };

      $http.post('/apiGetPersonalityInsights/', formData, {
        headers: {
          'Content-Type': 'application/json',
        }
      }).then(function (response) {
        $scope.personalityInsights = response.data;
        $scope.showForm = false; // Hide the form after submission

      }).catch(function (error) {
        $scope.errTitle = "Failed!";
        $scope.errMessage = "Please try again later.";
        let toastEl = new bootstrap.Toast(document.getElementById("errToast"));
        toastEl.show();
      });


    };

    $scope.prevTrait = function () {
      const back = () => {
        if ($scope.currentIndex > 0) {
          $scope.currentIndex--;
          $scope.currentTrait = $scope.traitOrder[$scope.currentIndex];
        }
      };

      const el = document.querySelector('.fade-slide');
      el.classList.remove('show');
      setTimeout(() => {
        $scope.$apply(back);
        el.classList.add('show');
      }, 300);
    };

    // Keyboard navigation
    document.addEventListener("keydown", function (e) {
      if (!$scope.currentTrait) return;

      if (e.key >= "1" && e.key <= "5") {
        $scope.$apply(() => {
          $scope.userInput[$scope.currentTrait] = parseInt(e.key);
        });
      } else if (e.key === "ArrowRight") {
        $scope.$apply($scope.nextTrait);
      } else if (e.key === "ArrowLeft") {
        $scope.$apply($scope.prevTrait);
      }
    });

    $timeout(() => {
      document.querySelector('.fade-slide').classList.add('show');
    });
    

  }
]);
