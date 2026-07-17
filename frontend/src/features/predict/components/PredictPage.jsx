import React, { useState } from 'react';
import PredictForm from './PredictForm';
import { predictService } from '../../../services/predictorService';

const PredictPage = () => {
    const [predictionResult, setPredictionResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState(null);

    const handlePredictPrice = async (dataInput) => {
        setIsLoading(true);
        setErrorMsg(null);
        setPredictionResult(null);
        try {
            const result = await predictService.predictPrice(dataInput);
            setPredictionResult(result);
        } catch (error) {
            setErrorMsg(error.message || 'Lỗi xử lý hệ thống.');
        } finally {
            setIsLoading(false);
        }
    };

    const formatPrediction = (prediction) => {
        if (!prediction) return '';

        const rawValue = Number(prediction.predicted_price);
        const normalizedValue = prediction.unit === 'Tỷ VNĐ' && rawValue < 1000 ? rawValue * 1_000_000_000 : rawValue;

        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND',
            maximumFractionDigits: 0
        }).format(normalizedValue);
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
            <div className="md:col-span-12 text-center md:text-left mb-2">
                <h1 className="text-3xl font-extrabold tracking-tight text-[#0F172A] md:text-4xl">
                    Kiểm định giá phù hợp thị trường
                </h1>
                <p className="text-sm text-slate-500 mt-2">
                    Hệ thống đối chiếu thông số bất động sản độc lập, giúp bạn kiểm tra xem mức giá rao bán có đang phù hợp với thực tế hay không.
                </p>
            </div>

            <div className="md:col-span-5">
                <PredictForm onPredict={handlePredictPrice} isLoading={isLoading} />
            </div>

            <div className="md:col-span-7 bg-white p-8 rounded-2xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.02)] min-h-[460px] flex flex-col justify-between">
                <div>
                    <h2 className="text-md font-semibold text-[#0F172A] border-b border-slate-100 pb-3">Kết quả thẩm định</h2>
                    <p className="text-xs text-slate-400 mt-3 leading-relaxed">
                        Giá trị bất động sản được mô phỏng ngầm thông qua cấu trúc học máy tích hợp, tính toán trọng số vị trí địa lý dựa trên hệ thống cơ sở dữ liệu Aura Realestate.
                    </p>
                </div>

                <div className="my-8 flex-1 flex flex-col justify-center items-center">
                    {isLoading && (
                        <div className="flex flex-col items-center space-y-3">
                            <div className="w-8 h-8 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"></div>
                            <p className="text-xs italic text-blue-600 font-medium">Đang chạy imputation và nạp đặc trưng...</p>
                        </div>
                    )}

                    {predictionResult !== null && !isLoading && (
                        <div className="w-full bg-emerald-50/50 border border-emerald-100 p-6 rounded-2xl text-center shadow-inner">
                            <span className="block text-xs font-bold text-emerald-700 uppercase tracking-widest mb-2">Giá dự đoán khuyến nghị</span>
                            <span className="text-3xl font-black text-emerald-600 tracking-tight font-mono">
                                {formatPrediction(predictionResult)}
                            </span>
                            <p className="mt-2 text-xs text-emerald-700">
                                Đơn vị đầu ra: {predictionResult.unit || 'Tỷ VNĐ'}
                            </p>
                        </div>
                    )}

                    {errorMsg && (
                        <div className="w-full p-4 bg-rose-50 border border-rose-100 rounded-xl text-xs text-rose-600 font-medium">
                            {errorMsg}
                        </div>
                    )}

                    {!isLoading && predictionResult === null && !errorMsg && (
                        <div className="text-slate-300 text-sm italic flex flex-col items-center">
                            <span className="text-3xl mb-1"></span>
                            Điền thông số bên trái để hiển thị biểu đồ định giá
                        </div>
                    )}
                </div>

                <div className="text-[11px] text-slate-400 flex justify-between items-center border-t border-slate-50 pt-4">
                    <span>_</span>
                    <span>_</span>
                </div>
            </div>
        </div>
    );
};

export default PredictPage;