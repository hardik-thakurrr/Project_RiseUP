app.factory("appService", [
  "$http",
  "$q",
  "$stateParams",
  function ($http, $stateParams, $q) {
    let ocrResult = [];
    let projectList = [];
    let projectDetail = {};
    let user = {};
    let resumes = [];

    return {

      getUser: function (){
        return user;
      },

      setOcrResult: function (data) {
        ocrResult = data;
      },

      getOcrResult: function () {
        return ocrResult;
      },

      setProjectList: function (data) {
        projectList = data;
      },

      getProjectList: function () {
        return projectList;
      },

      setProjectDetail: function (data) {
        projectDetail = data;
      },

      getProjectDetail: function () {
        return projectDetail;
      },

      getResumeFiles: function () {
        return resumes;
      },

      fetchUsername: function () {
        return $http
          .get("/apiGetUser/")
          .then(function (response) {
            if (response.data) {
              user = response.data;
              return user; 
            } else {
              return Promise.reject(error);
            }
          })
          .catch(function (error) {
            return Promise.reject(error);
          });
      },

      logout: function() {
        return $http.get('/apiLogout/')
            .then(function(response) {
                return response.data;
            })
            .catch(function(error) {
                return $q.reject(error);
            });
      },

      fetchProjects: function () {
        return $http
          .get("/apiProjects/")
          .then(function (response) {
            if (response.data) {
              projectList = response.data;
              return projectList; // Return project list (could be empty)
            } else {
              // This handles cases where the response is invalid but no error occurs
              return [];
            }
          })
          .catch(function (error) {
            // Reject the promise with the error to indicate failure
            return Promise.reject(error);
          });
      },

      fetchProjectTypes: function () {
        return $http
          .get("/apiget-options/")
          .then(function (response) {
            let options = response.data;
            return options;
          })
          .catch(function (error) {
            console.error("Error fetching options:", error);
            return Promise.reject(error);
          });
      },

      fetchResumeFiles: function () {
        return $http
          .get("/apiFetchResumes/")
          .then(function (response) {
            if (response.data) {
              resumes = response.data;
              return resumes;
            } else {
              return Promise.reject(error);
            }
          })
          .catch(function (error) {
            return Promise.reject(error);
          });
      },

      fetchResumeInsights: function (fileId) {
        return $http
          .get(`/apiGetResumeInsights/${fileId}`)
          .then(function (response) {
            if (response.data) {
              entry = response.data;
              return entry;
            } else {
              return Promise.reject(error);
            }
          })
          .catch(function (error) {
            return Promise.reject(error);
          });
      },

      startInterviewSession: function(fileId) {
        return $http.post(`/apiStartInterview/${fileId}`);
      },
      
      submitAudioResponse: function(interviewId, questionId, audioBlob) {
        const formData = new FormData();
        formData.append("interviewId", interviewId);
        formData.append("questionId", questionId);
        formData.append("audio", audioBlob);
      
        return $http.post("/apiSubmitAudioResponse", formData, {
          headers: { "Content-Type": undefined }
        });
      },
      
      validateInterview: function(interviewId) {
        return $http.post("/apiValidateInterview", { interviewId: interviewId });
      },
      
      fetchCoverLetter: function (fileId) {
        return $http
          .get(`/apiGetCoverLetter/${fileId}`)
          .then(function (response) {
            if (response.data) {
              entry = response.data;
              return entry;
            } else {
              return Promise.reject(error);
            }
          })
          .catch(function (error) {
            return Promise.reject(error);
          });
      },

    };
  },
]);
