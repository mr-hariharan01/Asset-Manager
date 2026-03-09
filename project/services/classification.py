def classify_department_and_priority(text):
    text = text.lower()
    department = 'General'
    priority = 'Low'
    if 'street light' in text or 'electricity' in text or 'streetlight' in text:
        department = 'Electricity Department'
        priority = 'Medium'
    elif 'garbage' in text or 'sanitation' in text or 'waste' in text:
        department = 'Sanitation Department'
        priority = 'High'
    elif 'road' in text or 'pothole' in text or 'damage' in text:
        department = 'Public Works Department'
        priority = 'Medium'
    elif 'water' in text or 'leak' in text or 'drainage' in text or 'pipe' in text:
        department = 'Water Supply Department'
        priority = 'High'

    if 'danger' in text or 'accident' in text or 'urgent' in text or 'safety' in text:
        priority = 'High'

    return department, priority
