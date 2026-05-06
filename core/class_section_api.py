# API endpoint to fetch sections for a class (for edit modal)
@csrf_exempt
@custom_login_required
def get_class_sections(request, class_id):
    """
    API endpoint to fetch sections for a specific class
    Returns JSON with section data
    """
    try:
        # Get school_id from session
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else None
        if not school_id:
            school_id = request.session.get('SchoolID')
        
        if not school_id:
            return JsonResponse({'error': 'School ID not found'}, status=400)
        
        # Fetch sections for the class
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_Section_List"(%s, %s)
            """, [school_id, class_id])
            sections = cursor.fetchall()
            
            # Format sections data
            sections_data = []
            for section in sections:
                sections_data.append({
                    'section_id': section[0],
                    'class_id': section[1],
                    'section_name': section[2],
                    'capacity': section[3],
                    'room_number': section[4],
                    'is_active': section[5]
                })
            
            return JsonResponse({'sections': sections_data})
    
    except Exception as e:
        logger.error(f"Error fetching sections for class {class_id}: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


