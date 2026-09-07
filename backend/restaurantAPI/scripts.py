from api.models import *

items = [
    {
        "title": "Pho Bo",
        "description": "Classic Vietnamese beef noodle soup with fragrant broth, rice noodles, and fresh herbs.",
        "category": 1,
        "featured": True,
        "price": 12.99,
        "stock": 10
    },
    {
        "title": "Pho Ga",
        "description": "Clear chicken broth with tender shredded chicken, rice noodles, and scallions.",
        "category": 1,
        "featured": False,
        "price": 9.49,
        "stock": 10
    },
    {
        "title": "Bun Bo Hue",
        "description": "Spicy central-Vietnam beef and pork noodle soup with lemongrass and chili oil.",
        "category": 1,
        "featured": False,
        "price": 14.25,
        "stock": 10
    },
    {
        "title": "Hu Tieu",
        "description": "Southern-style clear broth noodle soup with pork, shrimp, and crisp herbs.",
        "category": 1,
        "featured": True,
        "price": 11.75,
        "stock": 10
    },
    {
        "title": "Mi Quang",
        "description": "Turmeric rice noodles with shrimp, pork, peanuts, and a small savory broth.",
        "category": 1,
        "featured": False,
        "price": 8.99,
        "stock": 10
    },
    {
        "title": "Com Tam Suon",
        "description": "Broken rice served with grilled pork chop, pickles, and a fried egg.",
        "category": 2,
        "featured": False,
        "price": 10.50,
        "stock": 10
    },
    {
        "title": "Bun Cha",
        "description": "Grilled pork patties and slices served with rice vermicelli and fresh herbs.",
        "category": 2,
        "featured": True,
        "price": 13.40,
        "stock": 10
    },
    {
        "title": "Com Chien",
        "description": "Stir-fried rice with egg, vegetables, and choice of protein; served with scallions and lime.",
        "category": 2,
        "featured": False,
        "price": 12.00,
        "stock": 10
    },
    {
        "title": "Ca Kho To",
        "description": "Caramelized clay-pot fish in savory-sweet sauce, served with steamed rice.",
        "category": 2,
        "featured": False,
        "price": 7.99,
        "stock": 10
    },
    {
        "title": "Ga Nuong Sa",
        "description": "Lemongrass grilled chicken with fragrant marinade and jasmine rice.",
        "category": 2,
        "featured": False,
        "price": 15.00,
        "stock": 10
    },
    {
        "title": "Banh Mi Thit",
        "description": "Crispy baguette sandwich with savory pork, pickled vegetables, and cilantro.",
        "category": 2,
        "featured": True,
        "price": 9.75,
        "stock": 10
    },
    {
        "title": "Goi Cuon",
        "description": "Fresh spring rolls with shrimp, pork, rice vermicelli, and herbs; served with peanut sauce.",
        "category": 3,
        "featured": False,
        "price": 16.20,
        "stock": 10
    },
    {
        "title": "Cha Gio",
        "description": "Crispy fried spring rolls filled with pork and vegetables, served with nuoc cham.",
        "category": 3,
        "featured": True,
        "price": 12.30,
        "stock": 10
    },
    {
        "title": "Banh Xeo",
        "description": "Savory Vietnamese crepe stuffed with shrimp, pork, and bean sprouts; wrapped in lettuce.",
        "category": 3,
        "featured": False,
        "price": 10.99,
        "stock": 10
    },
    {
        "title": "Che Ba Mau",
        "description": "Three-color dessert with beans, jelly, coconut milk, and crushed ice.",
        "category": 3,
        "featured": True,
        "price": 18.50,
        "stock": 10
    },
    {
        "title": "Ca Phe Sua Da",
        "description": "Strong Vietnamese iced coffee brewed with sweetened condensed milk.",
        "category": 3,
        "featured": False,
        "price": 11.10,
        "stock": 10
    }
]


categories = [
    {
        "name": "Noodles and Soups",
        "slug": "noodles-soups"
    },
    {
        "name": "Rice and Plates",
        "slug": "rice-plates"
    },
    {
        "name": "Snacks and Drinks",
        "slug": "snacks-drinks"
    }
]

# Create new categories and items in the database
for cat in categories:
    # Check if the cat exists, ignore if yes
    if not Category.objects.filter(title=cat["name"]):
        Category.objects.create(title=cat["name"], slug=cat["slug"])

for item in items:
    # Check if the cat exists, ignore if yes
    if not MenuItem.objects.filter(title=item["title"]):
        MenuItem.objects.create(
            title=item["title"],
            description=item["description"],
            category_id=item["category"],
            featured=item["featured"],
            price=item["price"],
            stock=item["stock"]
        )


