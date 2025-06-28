import createApiClient from "./api.predict.service";

class VideoDetectService {
    constructor(baseUrl = "/api/videodetect/") {
        this.api = createApiClient(baseUrl);
    }
    async videoDetect(data) {
        const respone = await this.api.post("/", data);
        console.log("Response from videoDetect:", respone.data);
        return respone;
    }
}
export default new VideoDetectService();