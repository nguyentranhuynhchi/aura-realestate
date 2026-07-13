import React from 'react';
import { NavLink } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-white border-b border-slate-100 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo chữ P cách điệu như ảnh mẫu */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-[#2563EB] flex items-center justify-between p-1.5 shadow-sm shadow-blue-200">
            <span className="text-white text-md font-black mx-auto">A</span>
          </div>
          <span className="text-md font-bold tracking-tight text-[#0F172A]">
            AURA <span className="text-[#2563EB]">REALESTATE</span>
          </span>
        </div>

        {/* Thanh Menu mượt mà dạng Tab ngang */}
        <nav className="flex space-x-1 h-full items-center">
          <NavLink
            to="/predict"
            className={({ isActive }) =>
              `px-4 py-2 text-sm font-medium transition-all relative ${
                isActive
                  ? 'text-[#2563EB] after:absolute after:bottom-[-18px] after:left-0 after:right-0 after:h-[2px] after:bg-[#2563EB]'
                  : 'text-slate-500 hover:text-slate-900'
              }`
            }
          >
            Kiểm định giá thị trường
          </NavLink>

          <NavLink
            to="/chatbot"
            className={({ isActive }) =>
              `px-4 py-2 text-sm font-medium transition-all relative ${
                isActive
                  ? 'text-[#2563EB] after:absolute after:bottom-[-18px] after:left-0 after:right-0 after:h-[2px] after:bg-[#2563EB]'
                  : 'text-slate-500 hover:text-slate-900'
              }`
            }
          >
            Trợ lý tìm nhà & Pháp lý
          </NavLink>
        </nav>
      </div>
    </header>
  );
};

export default Header;