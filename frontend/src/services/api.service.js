import axios from "axios";

const commonConfig = {
    headers: {
        "Content-Type": "multipart/form-data; boundary=<calculated when request is sent>",
        Accept: "application/json",
    },
};
export default (baseURL) => {
    return axios.create({
        baseURL,
        ...commonConfig,
    });
};
