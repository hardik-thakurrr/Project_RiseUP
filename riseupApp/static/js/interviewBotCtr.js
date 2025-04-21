app.controller("InterviewBotController", [
  "$scope",
  "$http",
  "$stateParams",
  "appService",
  function ($scope, $http, $stateParams, appService) {
    $scope.questions = [];
    $scope.currentQuestionIndex = 0;
    $scope.currentQuestion = null;
    $scope.interviewId = null;
    $scope.recordedBlob = null;
    $scope.transcript = "";
    $scope.interviewComplete = false;

    $scope.progress = 0;  // percent
    $scope.progressLabel = "0 of 5 answered";

    $scope.startInterview = function () {
      const resumeId = $stateParams.resumeId ?? 1;

      appService.startInterviewSession(resumeId).then(function (data) {
        data = data.data;
        $scope.interviewId = data.interviewId;
        $scope.questions = Object.entries(data.questions);
        $scope.currentQuestion = $scope.questions[$scope.currentQuestionIndex];
      });
    };

    $scope.startRecording = function () {
      navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        source.connect(analyser);
        analyser.fftSize = 512;

        const bufferLength = analyser.fftSize;
        const dataArray = new Uint8Array(bufferLength);

        const canvas = document.getElementById("waveformCanvas");
        const canvasCtx = canvas.getContext("2d");

        function draw() {
          requestAnimationFrame(draw);

          analyser.getByteTimeDomainData(dataArray);

          canvasCtx.fillStyle = "white";
          canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

          canvasCtx.lineWidth = 3;
          canvasCtx.strokeStyle = "#2196F3"; // a friendly blue

          canvasCtx.beginPath();

          const sliceWidth = (canvas.width * 1.0) / bufferLength;
          let x = 0;

          for (let i = 0; i < bufferLength; i += 6) {  // <-- skip some points
            const v = dataArray[i] / 128.0;
            const y = (v * canvas.height) / 2;

            if (i === 0) {
              canvasCtx.moveTo(x, y);
            } else {
              canvasCtx.lineTo(x, y);
            }

            x += sliceWidth * 6; // adjust to match step
          }

          canvasCtx.lineTo(canvas.width, canvas.height / 2);
          canvasCtx.stroke();
        }

        draw(); // start animation loop

        const mediaRecorder = new MediaRecorder(stream);
        const chunks = [];

        mediaRecorder.ondataavailable = function (e) {
          chunks.push(e.data);
        };

        mediaRecorder.onstop = function () {
          const blob = new Blob(chunks, { type: "audio/wav" });
          $scope.recordedBlob = blob;
          $scope.uploadAudioResponse();

          // Stop drawing
          stream.getTracks().forEach(track => track.stop());
          audioContext.close();
        };

        mediaRecorder.start();
        console.log("Recording started...");

        $scope.mediaRecorder = mediaRecorder; // Store the mediaRecorder in the scope

      });
    };

    $scope.stopRecording = function () {
      if ($scope.mediaRecorder) {
        $scope.mediaRecorder.stop();
        console.log("Recording stopped.");
      }
    }

    $scope.uploadAudioResponse = function () {
      if (!$scope.recordedBlob || !$scope.currentQuestion) return;

      $scope.isProcessing = true;

      const [qid, qData] = $scope.currentQuestion;

      appService.submitAudioResponse($scope.interviewId, qid, $scope.recordedBlob)
        .then(function (data) {
          data = data.data;
          $scope.transcript = data.transcript;

          const total = $scope.questions.length;
          $scope.progress = Math.round((($scope.currentQuestionIndex + 1) / total) * 100);
          $scope.progressLabel = `${$scope.currentQuestionIndex + 1} of ${total} answered`;

          if (data.interviewComplete) {
            $scope.interviewComplete = true;
            $scope.getFinalReport();
          } else {
            $scope.nextQuestionPending = true;
            $scope.nextQuestionData = data;
          }
        }).finally(function () {
          $scope.isProcessing = false;
        });
    };

    $scope.showNextQuestion = function () {
      $scope.currentQuestionIndex++;
      $scope.currentQuestion = $scope.questions[$scope.currentQuestionIndex];
      $scope.transcript = "";
      $scope.nextQuestionPending = false;
    };

    $scope.getFinalReport = function () {
      appService.validateInterview($scope.interviewId).then(function (data) {
        data = data.data;
        $scope.interviewSummary = data;
        $scope.convertPathToBlob($scope.interviewSummary.reportPath);
      });
    };

    // Load the original uploaded file (pdf or image)
    $scope.convertPathToBlob = function (filePath) {
      $http({
        method: 'GET',
        url: filePath,
        responseType: 'blob'
      }).then(function (response) {
        const contentType = response.headers('Content-Type');
        const blob = new Blob([response.data], { type: contentType });
        const fileURL = URL.createObjectURL(blob);
        $scope.fileUrl = fileURL;
      }, function (error) {
        console.error("Error fetching uploaded file:", error);
      });
    };
  }
]);
