<template>
  <div class="p-4 container">
    <h2 class="text-xl font-bold mb-2">Upload Video for YOLO Detection</h2>

    <!-- Video Upload Section -->
    <div class="mb-4">
      <input type="file" @change="onFileChange" accept="video/*" class="border p-2 rounded" />
      <button class="ml-2 px-4 py-2 rounded shadow" @click="uploadVideo" :disabled="!videoFile">
        Upload
      </button>
    </div>

    <!-- Video Preview -->
    <div v-if="videoUrl" class="mt-6 mb-6">
      <h3 class="text-lg font-semibold mb-2">Video Preview</h3>
      <video :src="videoUrl" controls class="video-preview" ref="videoPlayer"></video>
    </div>

    <!-- Detection Results -->
    <div v-if="results.length" class="mt-6 w-full">
      <h3 class="text-lg font-semibold mb-2 text-left mt-2">Detection Results</h3>
      <video :src="videoOutputUrl" controls class="video-preview" ref="videoPlayer"></video>
      <ul class="results-container mt-2">
        <li v-for="item in results" :key="item.time_second" class="result-item">
          <span class="font-medium">Giây thứ {{ item.time_second }}:</span>
          {{ formatInstruments(item.detected_instruments) }}
        </li>
      </ul>
      <div class="mt-2">
        <h3 class="text-lg font-semibold mb-2">Music Description</h3>
        <p v-if="music_description">{{ music_description }}</p>
        <p v-else>No description available.</p>
      </div>

      <!-- similar_videos -->
      <h3 class="text-lg font-semibold mb-2 text-left mt-2">Videos featuring similar types of instrument</h3>
      <div class="similar-video">
        <div v-for="(video, videoIndex) in similar_videos" :key="videoIndex" class="similar-video-item">
          <!-- Hiển thị video đầu tiên -->

          <div class="video-container">
            <video :src="video.video.video_url" controls class="video-preview" ref="videoPlayer"></video>
          </div>

          <!-- Nút điều khiển hiển thị -->
          <div @click="toggleDetails(videoIndex)" class="toggle-button">
            {{ showDetails[videoIndex] ? 'Thu nhỏ' : 'Xem thêm' }}
          </div>

          <!-- Phần thông tin chi tiết -->
          <div class="related-infor" v-show="showDetails[videoIndex]">
            <p><b>Detection Results</b></p>
            <ul class="results-container mt-2">
              <li v-for="item in video.video.time_detections" :key="item.time_second" class="result-item">
                <span class="font-medium">Giây thứ {{ item.time_second }}:</span>
                {{ formatInstruments(item.detected_instruments) }}
              </li>
            </ul>
            <p><b>Music Description</b></p>
            <div class="video-infor">{{ video.video.music_description }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import VideoDetectService from "../services/videodetect.service";

export default {
  data() {
    return {
      videoFile: null,
      videoUrl: null,
      results: [],
      videoOutputUrl: null,
      music_description: null,
      similar_videos: [],
      showDetails: [] // Mảng lưu trạng thái show/hidden của từng video
    }
  },
  created() {
    // Khởi tạo trạng thái khi component được tạo
    this.initializeShowDetails();
  },
  watch: {
    // Theo dõi thay đổi của similar_videos
    similar_videos() {
      this.initializeShowDetails();
    }
  },
  methods: {
    formatInstruments(instruments) {
      const instrumentNames = {
        'cong_chieng': 'cồng chiêng',
        'dan_bau': 'đàn bầu',
        'dan_co': 'đàn cò',
        'dan_da': 'đàn đá',
        'dan_day': 'đàn đáy',
        'dan_nguyet': 'đàn nguyệt',
        'dan_sen': 'đàn sến',
        'dan_t_rung': 'đàn t\'rưng',
        'dan_tinh': 'đàn tính',
        'dan_tranh': 'đàn tranh',
        'dan_ty_ba': 'đàn tỳ bà',
        'guitar': 'guitar',
        'khen': 'khèn',
        'trong_quan': 'trống quân'
      };

      return instruments.map(instr => instrumentNames[instr] || instr).join(', ');
    },
    // Khởi tạo mảng trạng thái
    initializeShowDetails() {
      this.showDetails = this.similar_videos.map(() => false);
    },

    // Chuyển đổi trạng thái hiển thị
    toggleDetails(index) {
      const newShowDetails = [...this.showDetails];
      // Đóng tất cả các mục khác trước khi mở mục hiện tại
      if (!newShowDetails[index]) {
        newShowDetails.fill(false);
      }
      newShowDetails[index] = !newShowDetails[index];
      this.showDetails = newShowDetails;
    },
    onFileChange(event) {
      // Xóa URL cũ nếu có
      if (this.videoUrl) {
        URL.revokeObjectURL(this.videoUrl);
      }

      if (event.target.files && event.target.files[0]) {
        this.videoFile = event.target.files[0];
        // Tạo URL để hiển thị video
        this.videoUrl = URL.createObjectURL(this.videoFile);
      } else {
        this.videoFile = null;
        this.videoUrl = null;
      }
    },
    async uploadVideo() {
      if (!this.videoFile) return

      const form = new FormData()
      form.append('video', this.videoFile)

      try {
        const response = await VideoDetectService.videoDetect(form)
        this.results = response.data.time_detections;
        this.videoOutputUrl = response.data.video_url;
        this.music_description = response.data.music_description;
        this.similar_videos = response.data.similar_videos;
      } catch (error) {
        console.error(error)
        alert('Upload or detection failed.')
      }
    }
  },
  beforeUnmount() {
    // Dọn dẹp URL khi component bị hủy
    if (this.videoUrl) {
      URL.revokeObjectURL(this.videoUrl);
    }
  }
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.video-preview {
  width: 100%;
  max-width: 800px;
  height: auto;
  border: 1px solid #ccc;
  border-radius: 8px;
}

/* Thêm CSS mới cho phần kết quả */
.results-container {
  list-style-type: disc;
  background-color: #f9fafb;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  text-align: left;
  /* Căn trái nội dung */
  margin-left: 0;
  /* Loại bỏ margin trái */
  padding-left: 2rem;
  /* Tạo khoảng cách cho bullet */
  width: 100%;
  max-width: 800px;
  /* Giới hạn chiều rộng */
}

.result-item {
  margin-bottom: 0.5rem;
  text-align: left;
  /* Đảm bảo căn trái từng mục */
}

/* Đảm bảo phần kết quả căn trái toàn bộ */
.mt-6.w-full {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  /* Căn trái toàn bộ khối */
  width: 100%;
  max-width: 800px;
  /* Giống với video preview */
}

.similar-video {
  display: flex;
  gap: 5px;
  align-items: flex-start; /* cho items bắt đầu từ trên cùng */
}

.similar-video-item {
  background-color: #f0f0f0;
  padding: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  min-width: 150px;
  display: flex;
  flex-direction: column;
  /* cho phép auto chiều cao */
  height: auto !important;
  align-self: flex-start; /* tự co dãn theo nội dung */
}

.video-container {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-bottom: 10px;
}


/* ======================================== */
.toggle-button {
  cursor: pointer;
  color: #3498db;
  font-weight: 500;
  padding: 8px 0;
  transition: all 0.3s ease;
  user-select: none;
}

.toggle-button:hover {
  color: #2980b9;
  text-decoration: underline;
}

.related-infor {
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 15px;
}
</style>