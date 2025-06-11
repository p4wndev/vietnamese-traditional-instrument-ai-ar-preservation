import createApiClient from "./api.service";

class PredictService {
    constructor(baseUrl = "/api/detect/") {
        this.api = createApiClient(baseUrl);
    }
    async uploadImage(data) {
        const respone = await this.api.post("/", data);
        console.log(respone.data);
        return respone;
    }
    async getOntologyInfor(one_class_name) {
        const respone = await this.api.get(`/${one_class_name}`);
        console.log(respone.data);
        return respone;
    }
}
export default new PredictService();