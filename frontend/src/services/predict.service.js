import createApiClient from "./api.predict.service";

class PredictService {
    constructor(baseUrl = import.meta.env.VITE_API_URL
        ? `${import.meta.env.VITE_API_URL}/api`
        : "/api") {
        this.api = createApiClient(baseUrl);
    }
    async uploadImage(data) {
        const response = await this.api.post("/detect/image", data);
        return response;
    }
    async getOntologyInfor(one_class_name) {
        const response = await this.api.get(`/ontology/${one_class_name}`);
        return response;
    }
}
export default new PredictService();