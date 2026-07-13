import React, { useState } from 'react';

const DISTRICT_OPTIONS = [
    'Huyện Cần Giờ', 'Huyện Củ Chi', 'Huyện Hóc Môn', 'Huyện Nhà Bè', 'Huyện Bình Chánh',
    'Quận 6', 'Quận 4', 'Quận 11', 'Quận 5', 'Quận 8', 'Quận 9', 'Quận 3', 'Quận 10', 'Quận 2',
    'Quận Tân Phú', 'Quận Tân Bình', 'Quận Phú Nhuận', 'Quận Gò Vấp', 'Quận Bình Thạnh',
    'Quận 12', 'Quận 7', 'TP. Thủ Đức', 'Quận 1'
];

const INTERIOR_OPTIONS = [
    'Khác / Thỏa thuận', 'Nội thất cơ bản', 'Không nội thất', 'Không rõ (NaN)', 'Đầy đủ nội thất', 'Bàn giao thô'
];

const LEGAL_OPTIONS = ['Không rõ', 'Chưa Sổ / HDMB', 'Có Sổ'];

const DIRECTION_OPTIONS = ['Bắc', 'Nam', 'Tây', 'Tây Bắc', 'Tây Nam', 'Đông', 'Đông Bắc', 'Đông Nam'];

const PredictForm = ({ onPredict, isLoading }) => {
    const [formData, setFormData] = useState({
        area_raw: '',
        floors: '1',
        bathrooms: '1',
        district_clean: 'Quận 9',
        legal_clean: 'Không rõ',
        direction_clean: 'Đông',
        interior_clean: 'Không rõ (NaN)'
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!formData.area_raw || parseFloat(formData.area_raw) <= 0 || isLoading) return;
        onPredict({
            area_raw: parseFloat(formData.area_raw),
            floors: parseInt(formData.floors, 10),
            bathrooms: parseInt(formData.bathrooms, 10),
            district_clean: formData.district_clean,
            legal_clean: formData.legal_clean,
            direction_clean: formData.direction_clean,
            interior_clean: formData.interior_clean
        });
    };

    return (
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-2xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.02)] space-y-5">
            <div>
                <h3 className="text-base font-semibold text-[#0F172A]">Thông số bất động sản</h3>
                <p className="text-xs text-slate-400 mt-0.5">Cung cấp dữ liệu để mô hình AI phân tích chính xác</p>
            </div>

            <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Diện tích (m²)</label>
                <input
                    type="number"
                    name="area_raw"
                    value={formData.area_raw}
                    onChange={handleChange}
                    disabled={isLoading}
                    placeholder="Ví dụ: 75.5"
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 outline-none transition-all focus:border-[#2563EB] focus:bg-white focus:ring-4 focus:ring-blue-50"
                />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">Số tầng</label>
                    <select
                        name="floors"
                        value={formData.floors}
                        onChange={handleChange}
                        disabled={isLoading}
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 outline-none focus:border-[#2563EB] focus:bg-white"
                    >
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                            <option key={num} value={num}>{num} tầng</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">Số phòng tắm</label>
                    <select
                        name="bathrooms"
                        value={formData.bathrooms}
                        onChange={handleChange}
                        disabled={isLoading}
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 outline-none focus:border-[#2563EB] focus:bg-white"
                    >
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15].map((num) => (
                            <option key={num} value={num}>{num} phòng</option>
                        ))}
                    </select>
                </div>
            </div>

            <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Khu vực (Quận / Huyện)</label>
                <select
                    name="district_clean"
                    value={formData.district_clean}
                    onChange={handleChange}
                    disabled={isLoading}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 outline-none focus:border-[#2563EB] focus:bg-white"
                >
                    {DISTRICT_OPTIONS.map((district) => (
                        <option key={district} value={district}>{district}</option>
                    ))}
                </select>
            </div>

            <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Tình trạng pháp lý</label>
                <select
                    name="legal_clean"
                    value={formData.legal_clean}
                    onChange={handleChange}
                    disabled={isLoading}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 outline-none focus:border-[#2563EB] focus:bg-white"
                >
                    {LEGAL_OPTIONS.map((item) => (
                        <option key={item} value={item}>{item}</option>
                    ))}
                </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">Hướng nhà</label>
                    <select
                        name="direction_clean"
                        value={formData.direction_clean}
                        onChange={handleChange}
                        disabled={isLoading}
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 outline-none focus:border-[#2563EB] focus:bg-white"
                    >
                        {DIRECTION_OPTIONS.map((direction) => (
                            <option key={direction} value={direction}>{direction}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1.5">Tình trạng nội thất</label>
                    <select
                        name="interior_clean"
                        value={formData.interior_clean}
                        onChange={handleChange}
                        disabled={isLoading}
                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 outline-none focus:border-[#2563EB] focus:bg-white"
                    >
                        {INTERIOR_OPTIONS.map((interior) => (
                            <option key={interior} value={interior}>{interior}</option>
                        ))}
                    </select>
                </div>
            </div>

            <button
                type="submit"
                disabled={!formData.area_raw || isLoading}
                className="w-full py-3.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-medium rounded-xl text-sm transition-all shadow-md shadow-blue-100 disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none cursor-pointer"
            >
                {isLoading ? 'Đang tính toán kết quả...' : 'Kích hoạt mô hình định giá'}
            </button>
        </form>
    );
};

export default PredictForm;