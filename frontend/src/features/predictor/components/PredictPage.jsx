import React, { useState } from 'react';
import PredictForm from './PredictForm';
import { predictService } from '../../../services/predictorService';

const PredictPage = () => {
    const [resultPrice, setResultPrice] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState(null);

    const handlePredictPrice = async (dataInput) => {
        setIsLoading(true);
        setErrorMsg(null);
        setResultPrice(null);

        try {
            const price = await predictService.predictPrice(dataInput);
            setResultPrice(price);
        } catch (error) {
            // SỬA DÒNG NÀY: Kiểm tra nếu là Object thì ép thành chuỗi chữ đọc được
            const message = error.message && typeof error.message === 'object' 
                ? JSON.stringify(error.message) 
                : String(error.message || 'Lỗi kết nối máy chủ AI.');
            setErrorMsg(message);
        } finally {
            setIsLoading(false);
        }
    };

    // Hàm tiện ích chạy ngầm giúp format số tiền mặt cho đẹp mắt (Ví dụ: 3,500,000,000 VND)
    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
    };

    return (
        <div className="max-w-4xl mx-auto my-4 grid grid-cols-1 md:grid-cols-2 gap-6 p-4">
            {/* Cột trái: Form nhập liệu */}
            <div>
                <PredictForm onPredict={handlePredictPrice} isLoading={isLoading} />
            </div>

            {/* Cột phải: Khu vực bảng hiển thị kết quả */}
            <div className="flex flex-col justify-between p-6 bg-gradient-to-br from-gray-900 to-slate-800 text-white rounded-xl shadow-md border border-gray-700 min-h-[300px]">
                <div>
                    <h2 className="text-lg font-semibold border-b border-gray-700 pb-2 text-blue-400">Kết quả phân tích định giá</h2>
                    <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                        Thông số được phân tích qua thuật toán học máy kết hợp nhiều mô hình (Stacking Regressor), dựa trên tập dữ liệu bất động sản Aura Realestate thực tế.
                    </p>
                </div>

                {/* Khu vực hiện số tiền động */}
                <div className="my-6 text-center">
                    {isLoading && (
                        <div className="text-sm italic text-blue-300 animate-pulse">
                            Đang chạy imputation và nạp vector đặc trưng...
                        </div>
                    )}
                    
                    {resultPrice !== null && !isLoading && (
                        <div>
                            <span className="block text-xs text-gray-400 uppercase tracking-wider mb-1">Giá trị dự báo dự kiến</span>
                            <span className="text-3xl font-bold text-green-400 font-mono">
                                {formatCurrency(resultPrice)}
                            </span>
                        </div>
                    )}

                    {errorMsg && (
                        <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-xs text-red-300">
                            {errorMsg}
                        </div>
                    )}

                    {!isLoading && resultPrice === null && !errorMsg && (
                        <div className="text-sm text-gray-500 italic">
                            Vui lòng nhập thông số và bấm nút kích hoạt ở cột bên trái.
                        </div>
                    )}
                </div>

                <div className="text-[10px] text-gray-500 text-center border-t border-gray-800 pt-2">
                    Sai số mô hình ước tính: ±5% tùy biến động thị trường.
                </div>
            </div>
        </div>
    );
};

export default PredictPage;