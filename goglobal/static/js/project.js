function audioRecorder() {
    return {
      isRecording: false,
      mediaRecorder: null,
      audioChunks: [],

      async toggleRecording() {
          if (!this.isRecording) {
          // Start Recording
          await this.startRecording();
        } else {
          // Stop Recording
          this.stopRecording();
        }
      },

      async startRecording() {
        // Request the user's microphone
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);

        // Reset chunks
        this.audioChunks = [];

        // Start recording and handle data
        this.mediaRecorder.ondataavailable = (event) => {
          this.audioChunks.push(event.data);
        };

        // Set state to recording
        this.isRecording = true;

        // Start the MediaRecorder
        this.mediaRecorder.start();
      },

      stopRecording() {
        this.mediaRecorder.stop();
        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
          const reader = new FileReader();
          reader.onloadend = () => {
            document.getElementById('audio-data').value = reader.result.split(',')[1];
            this.$nextTick(() => {
                this.$refs.submitBtn.click()
          });
          };
          reader.readAsDataURL(audioBlob);
        };

        // Reset state
        this.isRecording = false;
      },

      cancelRecording() {
        if (this.isRecording) {
          // Stop the current recording without saving
          this.mediaRecorder.stop();
          this.audioChunks = [];
          this.isRecording = false;
          document.getElementById('audio-data').value = ''
        }
      }
    };
  }
