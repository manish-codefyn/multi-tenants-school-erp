# CORRECTED FORM FIELDS BASED ON MODELS

# AcademicYear Model Fields: name, code, start_date, end_date, is_current, has_terms
# REMOVE: description
# ADD: has_terms

# Term Model Fields: academic_year, name, term_type, order, start_date, end_date, is_current  
# REMOVE: code, description
# ADD: term_type

# SchoolClass Model Fields: name, numeric_name, code, level, order, pass_percentage, max_strength, tuition_fee, class_teacher, is_active
# REMOVE: description, capacity
# ADD: numeric_name, pass_percentage, max_strength, tuition_fee (capacity should be max_strength)

# Section Model Fields: class_name, name, code, max_strength, section_incharge, room_number, is_active
# REMOVE: description, capacity
# ADD: section_incharge, room_number (capacity should be max_strength)

# House Model Fields: name, code, color, motto, description, house_master, total_points, logo
# ADD: house_master, total_points
# Note: is_active comes from BaseModel

# HousePoints Model Fields: house, points, activity, description, date_awarded, awarded_by
# REMOVE: student, point_type, reason, awarded_date
# ADD: activity, description (reason->activity, awarded_date->date_awarded)

# Subject Model Fields: name, code, subject_type, subject_group, description, has_practical, has_project, is_scoring, credit_hours, max_marks, pass_marks, is_active
# REMOVE: is_core, is_elective  
# ADD: subject_group, has_practical, has_project, is_scoring, credit_hours, max_marks, pass_marks

# ClassSubject Model Fields: class_name, subject, is_compulsory, periods_per_week, teacher, academic_year
# REMOVE: is_optional, order
# ADD: is_compulsory, periods_per_week

# TimeTable Model Fields: class_name, section, academic_year, day, period_number, start_time, end_time, subject (ClassSubject FK), teacher, room, period_type
# CHANGE: room_number -> room
# ADD: period_type

# Holiday Model Fields: name, holiday_type, start_date, end_date, description, academic_year, affected_classes (M2M)
# REMOVE: is_recurring
# Note: affected_classes is ManyToMany, handle in form

# StudyMaterial Model Fields: title, material_type, description, class_name, subject, file, file_size, uploaded_by, is_published, publish_date
# REMOVE: tags
# Note: file_size and uploaded_by are auto-handled

# Syllabus Model Fields: class_name, subject, academic_year, topics (JSON), recommended_books, reference_materials, assessment_pattern (JSON)
# REMOVE: title, description, file, is_active
# ADD: topics, recommended_books, reference_materials, assessment_pattern

# Stream Model Fields: name, code, description, available_from_class, subjects (M2M), is_active
# CHANGE: class_name -> available_from_class
# ADD: subjects (ManyToMany)

# ClassTeacher Model Fields: class_name, section, teacher, academic_year, start_date, end_date, is_active
# ADD: start_date, end_date
