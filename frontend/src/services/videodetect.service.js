import createApiClient from "./api.predict.service";

class VideoDetectService {
    constructor(baseUrl = import.meta.env.VITE_API_URL
        ? `${import.meta.env.VITE_API_URL}/api`
        : "/api") {
        this.api = createApiClient(baseUrl);
    }
    async videoDetect(data) {
        const response = await this.api.post("/video/detect", data);
        return response;
    }
}
export default new VideoDetectService();