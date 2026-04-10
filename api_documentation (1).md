# API Documentation

## Authentication
### Login to get Auth Token
**POST** `https://api.abdullah-habashy.com/v1/academy/auth/login`

#### Request Body
```json
{
  "identifier": "abdelrahmanmostafa785@gmail.com",
  "password": "password"
}
```

#### Response Example
```json
{
  "success": true,
  "message": "تم تسجيل الدخول بنجاح.",
  "data": {
    "token": "11|4TcAJSbrbGNLnFxeDr4DX65BMW5HE3boo16zRgVBed96c629",
    "user": {
      "id": 2,
      "name": "Super Admin",
      "email": "abdelrahmanmostafa785@gmail.com"
    }
  },
  "code": 200
}
```

Use the token in all requests via header:
```
Authorization: Bearer {token}
```

---

## Students
### Get All Students
**GET** `https://api.abdullah-habashy.com/v1/academy/admin/students`

#### Filters
```
?filter[search]=STU800
?filter[level_id]=10
?filter[governorate_id]=1
```

#### Sorting
```
?sort=name
?sort=-updated_at
?sort=phone
```

#### Pagination
```
?page=1
?page=1&per_page=10
```

#### Response Example
*(Shortened for readability)*
```json
{
  "success": true,
  "message": "تم الحصول على البيانات بنجاح.",
  "data": {
    "data": [
      {
        "id": 102,
        "name": "ليلى محمود",
        "avatar": "https://api.demo-dev.tafra-tech.com/images/avatar.png",
        "phone": "01552449540",
        "parent_phone": "01212859251",
        "status": "active",
        "rate": "2.47",
        "code": "22157197",
        "educational_level": "الصف الثالث الابتدائي",
        "telegram_username": "لم يتم الربط"
      }
    ],
    "links": { ... },
    "meta": { ... }
  },
  "code": 200
}
```

---

## Student Bootcamps
### Enrollment History for a Student
**GET** `https://api.abdullah-habashy.com/v1/academy/admin/bootcamps/student/{student}/enrollmentHistory?page=1&items_per_page=10`

#### Response Example
```json
{
  "success": true,
  "message": "تم الحصول على البيانات بنجاح.",
  "data": {
    "data": [
      {
        "id": 302,
        "bootcamp_id": 16,
        "bootcamp_name": "مجموعة علم النفس المكثف",
        "semester_name": "الفصل الدراسي الأول",
        "type": "تسجيل",
        "can_watch_in_days": 180,
        "days_left": 177,
        "created_at": "2025-12-09 19:18"
      }
    ],
    "links": { ... },
    "meta": { ... },
    "student_time_bucket": 0
  },
  "code": 200
}
```

---

## Bootcamps
### Get All Bootcamps
**GET** `https://api.abdullah-habashy.com/v1/academy/admin/bootcamps`

#### Filters
```
?filter[name]=name
?filter[material_id]=1
?filter[educational_level_id]=1
?filter[bootcamp_category_id]=1
```

#### Sorting
```
?sort=name
?sort=price
?sort=publish_date
?sort=publish_status
```

#### Response Example
```json
{
  "success": true,
  "message": "تم الحصول على البيانات بنجاح.",
  "data": {
    "data": [
      {
        "id": 20,
        "name": "برنامج علوم البيانات التأسيسي",
        "instructor": "رنا سالم",
        "price": "399.00",
        "price_currency": "EGP",
        "platform_types": ["web"],
        "publish_status": "draft",
        "publish_date": null,
        "material": "الدراسات الثانوية",
        "educational_level": "الصف الرابع الابتدائي",
        "bootcamp_category": "ابواب",
        "duration_in_seconds": 66834,
        "count_of_questions": 279,
        "thumbnail": "https://api.demo-dev.tafra-tech.com/images/bootcamp-holder.webp",
        "count_of_enrolled_students": 20
      }
    ]
  }
}
```

---

# End of API Documentation

