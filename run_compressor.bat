@echo off
chcp 65001 >nul
title Auto Compressor & Uploader

echo ======================================================
echo      Starting Video Compressor & Uploader...
echo ======================================================

:: الانتقال إلى مجلد الكود لضمان قراءة ملف الإعدادات بشكل صحيح
cd /d "e:\HABASHY\Python Codes"

:: تشغيل الكود
python "compressUpload.py"

:: إبقاء الشاشة مفتوحة في حالة حدوث خطأ أو إغلاق الكود
echo.
echo Script stopped. Press any key to exit...
pause >nul
