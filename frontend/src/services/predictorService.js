import api from './api';

export const predictService = {
    /**
     * Gửi các thông số nhà đất sang FastAPI để mô hình Học máy tính toán giá.
     * @param {Object} inputData - Object chứa diện tích, số phòng, vị trí...
     * @returns {Promise<{predicted_price: number, unit: string}>} - Giá nhà dự kiến và đơn vị trả về.
     */
    predictPrice: async (inputData) => {
        try {
            const response = await api.post('/api/v1/predict', inputData);

            if (response.data && response.data.success) {
                return {
                    predicted_price: response.data.data.predicted_price,
                    unit: response.data.data.unit || 'Tỷ VNĐ'
                };
            }
            throw new Error('Cấu trúc dữ liệu phản hồi từ mô hình ML không hợp lệ.');
        } catch (error) {
            console.error('Error in predictService.predictPrice:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'Lỗi kết nối máy chủ AI.';
            throw new Error(errorMessage);
        }
    }
};