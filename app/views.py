from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.contrib import messages

from django.http import JsonResponse
from .models import SkinScan, Product, Routine, Cart, CartItem, Order, OrderItem
from .utils.image_processing import SkinImageProcessor
import random
import json
from datetime import datetime
import cv2 # Needed for imencode if we were to save the processed image manually, ensuring opencv is present

def index(request):
    return render(request, 'index.html')

def sign_in(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                # Redirect staff users to admin panel, regular users to home
                if user.is_staff:
                    return redirect('admin_dashboard')
                else:
                    return redirect('index')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'sign-in.html', {'form': form})

def sign_up(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return render(request, 'sign-up.html')
        
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'sign-up.html')
        
        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'sign-up.html')
        
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'sign-up.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'sign-up.html')
        
        # Create User
        user = User.objects.create_user(username=username, email=email, password=password1)
        
        # Save plain password to profile for testing
        if hasattr(user, 'profile'):
            user.profile.view_username = username
            user.profile.view_password = password1
            user.profile.save()
        
        login(request, user)
        return redirect('index')
        
    return render(request, 'sign-up.html')

@login_required
def profile_view(request):
    user = request.user
    scans = SkinScan.objects.filter(user=user).order_by('-scan_date')
    latest_scan = scans.first()
    
    # Get or create routine
    routine, created = Routine.objects.get_or_create(user=user)
    
    context = {
        'scans': scans,
        'latest_scan': latest_scan,
        'routine': routine,
    }
    return render(request, 'profile.html', context)

@login_required
def analysis_view(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        
        # 1. Initialize Processor
        processor = SkinImageProcessor()
        
        # 2. Run Pipeline
        success, result = processor.process_pipeline(image)
        
        if not success:
            return JsonResponse({
                'success': False,
                'message': result # Validate error message
            })
            
        # Note: 'result' is now the processed OpenCV image (numpy array).
        # We perform heuristic analysis on this processed image
        
        result_data = processor.analyze_skin(result)
        scores = result_data['scores']
        severities = result_data['severities']
        
        acne = scores['acne']
        oiliness = scores['oiliness']
        wrinkles = scores['wrinkles']
        hydration = scores['hydration']
        
        # Reset file pointer before saving to DB
        image.seek(0)
        
        # Recommendations
        from app.utils.recommendation_engine import RecommendationEngine
        rec_engine = RecommendationEngine() # Auto-seeds DB if needed
        recs = rec_engine.generate_recommendations(result_data)
        
        # Store analysis as JSON for detailed retrieval
        
        scan = SkinScan.objects.create(
            user=request.user,
            image=image,
            acne_score=acne,
            oiliness_score=oiliness,
            wrinkle_score=wrinkles,
            hydration_score=hydration,
            dark_circles_score=scores.get('dark_circles', 0),
            health_score=result_data['health_score'],
            skin_type=result_data['skin_type'],
            overall_analysis=json.dumps({
                'severities': severities,
                'recommendations': recs
            })
        )

        # Update User Routine
        try:
            user_routine, _ = Routine.objects.get_or_create(user=request.user)
            user_routine.morning_products.clear()
            user_routine.night_products.clear()
            
            for prod_data in recs.get('morning_routine', []):
                user_routine.morning_products.add(prod_data['id'])
                
            for prod_data in recs.get('night_routine', []):
                user_routine.night_products.add(prod_data['id'])
                
            user_routine.save()
        except Exception as e:
            print(f"Error saving routine: {e}")
        
        return JsonResponse({
            'success': True,
            'acne': acne,
            'oiliness': oiliness,
            'wrinkles': wrinkles,
            'hydration': hydration,
            'dark_circles': scores.get('dark_circles', 0),
            'skin_type': result_data['skin_type'],
            'health_score': result_data['health_score'],
            'severities': severities,
            'recommendations': recs,
            'scan_id': scan.id,
            'message': 'Analysis complete!'
        })
        
    return render(request, 'analysis.html')

@login_required
def scan_history(request):
    scans = SkinScan.objects.filter(user=request.user).order_by('-scan_date')
    return render(request, 'scan_history.html', {'scans': scans})

@login_required
def scan_detail(request, scan_id):
    try:
        scan = SkinScan.objects.get(id=scan_id, user=request.user)
        # Parse JSON results if stored
        try:
            extra_data = json.loads(scan.overall_analysis)
        except:
            extra_data = {}
            
        context = {
            'scan': scan,
            'extra_data': extra_data,
        }
        return render(request, 'scan_detail.html', context)
    except SkinScan.DoesNotExist:
        messages.error(request, "Scan not found.")
        return redirect('profile')

def shop_view(request):
    from django.db.models import Q
    
    # Get search query and filter from GET parameters
    search_query = request.GET.get('q', '').strip()
    skin_type_filter = request.GET.get('skin_type', '').strip()
    
    # Start with all products
    products = Product.objects.all()
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(skin_type_suitability__icontains=search_query)
        )
    
    # Apply skin type filter
    if skin_type_filter:
        products = products.filter(
            Q(skin_type_suitability__icontains=skin_type_filter) |
            Q(skin_type_suitability__icontains='All')
        )
    
    cart_product_ids = []
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_product_ids = list(cart.cartitem_set.values_list('product_id', flat=True))

    return render(request, 'shop.html', {
        'products': products,
        'cart_product_ids': cart_product_ids,
        'search_query': search_query,
        'skin_type_filter': skin_type_filter
    })


def single_product_view(request):
    product_id = request.GET.get('id')
    product = None
    in_cart = False
    
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            if request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
                if cart:
                    if cart.cartitem_set.filter(product=product).exists():
                        in_cart = True
        except Product.DoesNotExist:
            pass # Product remains None
            
    return render(request, 'single-product.html', {'product': product, 'in_cart': in_cart})

def sign_out(request):
    logout(request)
    messages.info(request, "You have successfully logged out.") 
    return redirect('sign_in')

@login_required
def routines_view(request):
    user = request.user
    routine, created = Routine.objects.get_or_create(user=user)
    products = Product.objects.all()[:6]  # Get some recommended products
    
    # Get latest scan for ingredients
    latest_scan = SkinScan.objects.filter(user=user).order_by('-scan_date').first()
    active_ingredients = []
    avoid_ingredients = []
    
    if latest_scan and latest_scan.overall_analysis:
        try:
            data = json.loads(latest_scan.overall_analysis)
            active_ingredients = data.get('recommendations', {}).get('active_ingredients', [])
            avoid_ingredients = data.get('recommendations', {}).get('avoid_ingredients', [])
        except:
            pass

    context = {
        'routine': routine,
        'active_ingredients': active_ingredients,
        'avoid_ingredients': avoid_ingredients,
        'products': products,
    }
    return render(request, 'routines.html', context)

@login_required
def progress_view(request):
    user = request.user
    # Fetch all scans for history
    scans = SkinScan.objects.filter(user=user).order_by('-scan_date')
    latest_scan = scans.first() if scans.exists() else None
    
    # Chart Data (Chronological)
    # We take up to 30 recent points for the graph, but reversed for time axis
    graph_scans = list(scans[:30])
    graph_scans.reverse() 
    
    dates = [s.scan_date.strftime('%Y-%m-%d') for s in graph_scans]
    acne_trend = [s.acne_score for s in graph_scans]
    oiliness_trend = [s.oiliness_score for s in graph_scans]
    hydration_trend = [s.hydration_score for s in graph_scans]
    wrinkles_trend = [s.wrinkle_score for s in graph_scans]

    # Analysis & Comparison (Latest vs First)
    insights = []
    if len(scans) > 1:
        first_scan = scans.last()
        
        # Hydration Improvement
        hyd_diff = latest_scan.hydration_score - first_scan.hydration_score
        if hyd_diff > 0:
            insights.append({'type': 'success', 'icon': 'bx-droplet', 'text': f"Your skin hydration has improved by {hyd_diff}% since starting!"})
        elif hyd_diff < -5:
            insights.append({'type': 'warning', 'icon': 'bx-droplet', 'text': f"Hydration levels have dropped by {abs(hyd_diff)}%. Consider using a richer moisturizer."})
            
        # Acne Improvement (Lower is better)
        acne_diff = latest_scan.acne_score - first_scan.acne_score
        if acne_diff < 0:
            insights.append({'type': 'success', 'icon': 'bx-check-circle', 'text': f"Great job! Acne severity reduced by {abs(acne_diff)}%."})
        elif acne_diff > 5:
            insights.append({'type': 'danger', 'icon': 'bx-error-circle', 'text': "Acne flare-ups detected. Check 'Identify Ingredients' to see if a product is causing this."})

    # Stats for Cards
    if scans.exists():
        avg_acne = sum(s.acne_score for s in scans) / len(scans)
        avg_oiliness = sum(s.oiliness_score for s in scans) / len(scans)
        avg_hydration = sum(s.hydration_score for s in scans) / len(scans)
        avg_wrinkles = sum(s.wrinkle_score for s in scans) / len(scans)
        overall_health = (100 - avg_acne + avg_hydration + 100 - avg_oiliness + 100 - avg_wrinkles) / 4
    else:
        avg_acne = avg_oiliness = avg_hydration = avg_wrinkles = overall_health = 0
    
    context = {
        'scans': scans,
        'latest_scan': latest_scan,
        'avg_acne': round(avg_acne),
        'avg_oiliness': round(avg_oiliness),
        'avg_hydration': round(avg_hydration),
        'avg_wrinkles': round(avg_wrinkles),
        'overall_health': round(overall_health),
        # Graph Data JSON
        'dates': dates,
        'acne_trend': acne_trend,
        'oiliness_trend': oiliness_trend,
        'hydration_trend': hydration_trend,
        'wrinkles_trend': wrinkles_trend,
        'insights': insights
    }
    return render(request, 'progress.html', context)

# ==========================================
# E-commerce Views
# ==========================================

@login_required
def add_to_cart(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Updated quantity of {product.name}.")
        else:
            messages.success(request, f"Added {product.name} to cart.")
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
    
    return redirect('shop') # Redirect back to shop or cart

@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})

@login_required
def remove_from_cart(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id)
        if item.cart.user == request.user:
            item.delete()
            # messages.success(request, "Item removed.")
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')

@login_required
def checkout_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if cart.get_count() == 0:
        return redirect('shop')
        
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')
        
        # Mock Card Details (Not saved, but processed)
        card_name = request.POST.get('card_name')
        card_number = request.POST.get('card_number')
        card_expiry = request.POST.get('card_expiry')
        card_cvv = request.POST.get('card_cvv')
        
        # Simple Validation
        if not all([full_name, email, phone, address, card_number, card_expiry]):
             messages.error(request, "Please fill in all required billing and payment fields.")
             return render(request, 'checkout.html', {'cart': cart})

        # Create Order (Mock Payment Success)
        order = Order.objects.create(
            user=request.user,
            total_amount=cart.get_total_price(),
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            zip_code=zip_code,
            status='Paid', 
            is_paid=True
        )
        
        # Move items
        for item in cart.cartitem_set.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            product = Product.objects.get(id=item.product_id)
            product.qty = product.qty - item.quantity
            product.save()
        # Clear Cart
        cart.cartitem_set.all().delete()
        
        return redirect('order_success', order_id=order.id)
        
    return render(request, 'checkout.html', {'cart': cart})

@login_required
def order_success_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return redirect('index')
    return render(request, 'order_success.html', {'order': order})

@login_required
def increase_cart_item(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id)
        if item.cart.user == request.user:
            item.quantity += 1
            item.save()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')

@login_required
def decrease_cart_item(request, item_id):
    try:
        item = CartItem.objects.get(id=item_id)
        if item.cart.user == request.user:
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        
        # Capture basics
        profile.skin_type = request.POST.get('skin_type', profile.skin_type)
        age = request.POST.get('age')
        if age:
            profile.age = int(age)
            
        # Handle Image
        if request.FILES.get('profile_pic'):
            profile.profile_pic = request.FILES['profile_pic']
            
        profile.save()
        messages.success(request, "Profile updated successfully!")
        
    return redirect('profile')


# ==================== ADMIN PANEL VIEWS ====================

def admin_required(view_func):
    '''Decorator to restrict access to staff users only'''
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to continue.')
            return redirect('sign_in')
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_dashboard(request):
    from django.contrib.auth.models import User
    product_count = Product.objects.count()
    user_count = User.objects.count()
    scan_count = SkinScan.objects.count()
    order_count = Order.objects.count()
    
    recent_products = Product.objects.all().order_by('-created_at')[:5]
    
    context = {
        'product_count': product_count,
        'user_count': user_count,
        'scan_count': scan_count,
        'order_count': order_count,
        'recent_products': recent_products,
    }
    return render(request, 'admin/dashboard.html', context)

@admin_required
def admin_products_list(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'admin/products_list.html', {'products': products})

@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        brand = request.POST.get('brand', '')
        description = request.POST.get('description')
        price = request.POST.get('price')
        skin_type = request.POST.get('skin_type_suitability')
        benefits = request.POST.get('benefits')
        image = request.FILES.get('image')
        qty = request.POST.get('qty')
        # Validation
        if not all([name, price, description]):
            messages.error(request, 'Please fill all required fields (Name, Price, Description).')
            return render(request, 'admin/product_form.html')
        
        try:
            Product.objects.create(
                name=name,
                brand=brand,
                description=description,
                price=price,
                skin_type_suitability=skin_type or 'All',
                benefits=benefits or '',
                image=image,
                qty=qty,
            )
            messages.success(request, f"Product '{name}' added successfully!")
            return redirect('admin_products_list')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
            return render(request, 'admin/product_form.html')
    
    return render(request, 'admin/product_form.html', {'mode': 'add'})

@admin_required
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.brand = request.POST.get('brand', product.brand)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.skin_type_suitability = request.POST.get('skin_type_suitability', product.skin_type_suitability)
        product.benefits = request.POST.get('benefits', product.benefits)
        product.qty=request.POST.get('qty', product.qty)
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        
        try:
            product.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('admin_products_list')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    return render(request, 'admin/product_form.html', {'product': product, 'mode': 'edit'})

@admin_required
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    
    try:
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully.")
    except Exception as e:
        messages.error(request, f'Error deleting product: {str(e)}')
    
    return redirect('admin_products_list')

@login_required
def user_orders(request):
    """View for regular users to see their order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders})

@admin_required
def admin_users_list(request):
    """Admin view to see all users"""
    from django.contrib.auth.models import User
    # Optionally exclude superusers or the currently logged in admin so they don't delete themselves
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/users_list.html', {'users': users})

@admin_required
def admin_user_delete(request, user_id):
    """Admin view to delete a user"""
    from django.contrib.auth.models import User
    user_to_delete = get_object_or_404(User, id=user_id)
    
    if user_to_delete.is_superuser or user_to_delete == request.user:
        messages.error(request, "You cannot delete this admin user.")
    else:
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"User '{username}' has been deleted successfully.")
        
    return redirect('admin_users_list')

