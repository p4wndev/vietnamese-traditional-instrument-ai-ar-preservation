import createApiClient from "./api.rag.service";

class RagService {
    constructor(baseUrl = "/api/chatbot/rag/") {
        this.api = createApiClient(baseUrl);
    }
    async ragAnswer(question) {
        console.log("ragAnswer called with question:", question);
        const respone = await this.api.post("/", { question });
        console.log(respone.data);
        return respone.data;
    }
}
export default new RagService();