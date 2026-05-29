import createApiClient from "./api.rag.service";

class RagService {
    constructor(baseUrl = import.meta.env.VITE_API_URL
        ? `${import.meta.env.VITE_API_URL}/api`
        : "/api") {
        this.api = createApiClient(baseUrl);
    }
    async ragAnswer(question) {
        const response = await this.api.post("/chatbot/rag", { question });
        return response.data;
    }
}
export default new RagService();