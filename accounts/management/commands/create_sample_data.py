"""
Professional Sample Data Creation Command for Library Management System

This command creates realistic sample data for testing and development:
- Users with different roles
- Books with authors, categories, publishers
- Loans and reservations
- Analytics data
"""

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker

from accounts.models import UserRole, AccountStatus, VerificationStatus
from books.models import Book, Author, Category, Publisher
from analytics.models import ActivityLog, BookPopularity, SystemStatistics
from django.db import transaction

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Create sample data for library management system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=15,
            help='Number of users to create (default: 15)'
        )
        parser.add_argument(
            '--books',
            type=int,
            default=20,
            help='Number of books to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(
                self.style.WARNING('Clearing existing data...')
            )
            self.clear_data()

        self.stdout.write(
            self.style.SUCCESS('Creating sample data...')
        )

        # Create sample data
        try:
            with transaction.atomic():
                users = self.create_users(options['users'])
                categories = self.create_categories()
                authors = self.create_authors()
                publishers = self.create_publishers()
                books = self.create_books(options['books'], authors, categories, publishers)
                self.create_activity_logs(users, books)
                self.create_book_popularity(books)
                self.create_system_statistics()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample data: {e}')
            )
            raise e

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {len(users)} users\n'
                f'- {len(categories)} categories\n'
                f'- {len(authors)} authors\n'
                f'- {len(publishers)} publishers\n'
                f'- {len(books)} books\n'
                f'- Activity logs and analytics data'
            )
        )

    def clear_data(self):
        """Clear existing sample data"""
        # Clear in reverse order to avoid foreign key constraints
        ActivityLog.objects.all().delete()
        BookPopularity.objects.all().delete()
        SystemStatistics.objects.all().delete()
        Book.objects.all().delete()
        Author.objects.all().delete()
        Category.objects.all().delete()
        Publisher.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def create_users(self, count):
        """Create sample users with different roles"""
        users = []
        
        # Create admin users
        admin_user, created = User.objects.get_or_create(
            email='admin@library.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': UserRole.SUPER_ADMIN,
                'account_status': AccountStatus.ACTIVE,
                'email_verification_status': VerificationStatus.APPROVED,
                'phone_verification_status': VerificationStatus.APPROVED,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        users.append(admin_user)

        # Create librarian
        librarian, created = User.objects.get_or_create(
            email='librarian@library.com',
            defaults={
                'username': 'librarian',
                'first_name': 'John',
                'last_name': 'Librarian',
                'role': UserRole.LIBRARIAN,
                'account_status': AccountStatus.ACTIVE,
                'email_verification_status': VerificationStatus.APPROVED,
                'phone_verification_status': VerificationStatus.APPROVED,
                'profession_title': 'Head Librarian',
                'workplace_organization': 'Central Library'
            }
        )
        if created:
            librarian.set_password('librarian123')
            librarian.save()
        users.append(librarian)

        # Create teachers
        for i in range(3):
            teacher, created = User.objects.get_or_create(
                email=f'teacher{i+1}@school.com',
                defaults={
                    'username': f'teacher{i+1}',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': UserRole.TEACHER,
                    'account_status': AccountStatus.ACTIVE,
                    'email_verification_status': VerificationStatus.APPROVED,
                    'phone_verification_status': VerificationStatus.APPROVED,
                    'profession_title': 'Teacher',
                    'workplace_organization': fake.company(),
                    'phone_number': f'+998901234{i+10:03d}'
                }
            )
            if created:
                teacher.set_password('teacher123')
                teacher.save()
            users.append(teacher)

        # Create students
        for i in range(count - 5):
            student, created = User.objects.get_or_create(
                email=f'student{i+1}@student.com',
                defaults={
                    'username': f'student{i+1}',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': UserRole.STUDENT,
                    'account_status': random.choice([AccountStatus.ACTIVE, AccountStatus.PENDING_ACTIVATION]),
                    'email_verification_status': random.choice([VerificationStatus.APPROVED, VerificationStatus.PENDING]),
                    'date_of_birth': fake.date_of_birth(minimum_age=16, maximum_age=25),
                    'phone_number': f'+998901234{i+20:03d}',
                    'profession_title': 'Student',
                    'workplace_organization': 'University'
                }
            )
            if created:
                student.set_password('student123')
                student.save()
            users.append(student)

        return users

    def create_categories(self):
        """Create book categories"""
        categories_data = [
            ('Fiction', 'fiction', 'Fictional literature and novels'),
            ('Science', 'science', 'Scientific books and research'),
            ('Technology', 'technology', 'Technology and computer science'),
            ('History', 'history', 'Historical books and biographies'),
            ('Education', 'education', 'Educational and academic books'),
            ('Art', 'art', 'Art, design and creative books'),
            ('Business', 'business', 'Business and economics'),
            ('Health', 'health', 'Health and medical books'),
        ]
        
        categories = []
        for name, slug, description in categories_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': description, 'slug': slug}
            )
            categories.append(category)
        
        return categories

    def create_authors(self):
        """Create sample authors"""
        authors_data = [
            ('William Shakespeare', 'william-shakespeare', 'English playwright and poet'),
            ('J.K. Rowling', 'jk-rowling', 'British author of Harry Potter series'),
            ('Stephen King', 'stephen-king', 'American author of horror and suspense'),
            ('Agatha Christie', 'agatha-christie', 'British crime novelist'),
            ('George Orwell', 'george-orwell', 'British author and journalist'),
            ('Jane Austen', 'jane-austen', 'English novelist'),
            ('Mark Twain', 'mark-twain', 'American writer and humorist'),
            ('Charles Dickens', 'charles-dickens', 'English writer and social critic'),
            ('Ernest Hemingway', 'ernest-hemingway', 'American novelist and journalist'),
            ('Leo Tolstoy', 'leo-tolstoy', 'Russian writer'),
        ]
        
        authors = []
        for name, slug, biography in authors_data:
            author, created = Author.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slug,
                    'biography': biography,
                    'nationality': fake.country(),
                    'birth_date': fake.date_between(start_date='-100y', end_date='-20y'),
                }
            )
            authors.append(author)
            if created:
                self.stdout.write(f'  Created author: {author.name}')
        
        return authors

    def create_publishers(self):
        """Create sample publishers"""
        publishers_data = [
            ('Penguin Random House', 'penguin-random-house', 'New York, USA'),
            ('HarperCollins', 'harpercollins', 'New York, USA'),
            ('Macmillan Publishers', 'macmillan-publishers', 'London, UK'),
            ('Simon & Schuster', 'simon-schuster', 'New York, USA'),
            ('Hachette Book Group', 'hachette-book-group', 'New York, USA'),
            ('Scholastic Corporation', 'scholastic-corporation', 'New York, USA'),
            ('Pearson Education', 'pearson-education', 'London, UK'),
            ('Oxford University Press', 'oxford-university-press', 'Oxford, UK'),
        ]
        
        publishers = []
        for name, slug, address in publishers_data:
            publisher, created = Publisher.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slug,
                    'address': address,
                    'city': fake.city(),
                    'country': fake.country(),
                    'website': f'https://www.{slug}.com',
                    'email': f'info@{slug}.com',
                }
            )
            publishers.append(publisher)
            if created:
                self.stdout.write(f'  Created publisher: {publisher.name}')
        
        return publishers

    def create_books(self, count, authors, categories, publishers):
        """Create sample books"""
        books_data = [
            ('To Kill a Mockingbird', 'Classic novel about racial injustice'),
            ('1984', 'Dystopian social science fiction novel'),
            ('Pride and Prejudice', 'Romantic novel of manners'),
            ('The Great Gatsby', 'American classic about the Jazz Age'),
            ('Harry Potter and the Philosopher\'s Stone', 'Fantasy novel about a young wizard'),
            ('The Catcher in the Rye', 'Coming-of-age story'),
            ('Lord of the Flies', 'Allegorical novel about survival'),
            ('Animal Farm', 'Political satire about farm animals'),
            ('Brave New World', 'Dystopian novel about a futuristic society'),
            ('The Hobbit', 'Fantasy adventure novel'),
            ('Fahrenheit 451', 'Dystopian novel about book burning'),
            ('Jane Eyre', 'Gothic romance novel'),
            ('Wuthering Heights', 'Gothic novel about passionate love'),
            ('The Adventures of Huckleberry Finn', 'Adventure novel about a boy and a slave'),
            ('Moby Dick', 'Epic novel about a whale hunt'),
            ('War and Peace', 'Epic novel about Russian society'),
            ('Crime and Punishment', 'Psychological novel about guilt'),
            ('The Brothers Karamazov', 'Philosophical novel about faith'),
            ('Anna Karenina', 'Novel about aristocratic Russian society'),
            ('One Hundred Years of Solitude', 'Magical realism novel'),
        ]
        
        books = []
        for i, (title, description) in enumerate(books_data[:count]):
            # Generate slug from title
            slug = title.lower().replace(' ', '-').replace("'", '').replace('.', '')
            slug = f'{slug}-{i+1}'  # Add number to ensure uniqueness
            
            book, created = Book.objects.get_or_create(
                title=title,
                defaults={
                    'slug': slug,
                    'description': description,
                    'category': random.choice(categories),
                    'publisher': random.choice(publishers),
                    'isbn': f'978-{random.randint(1000000000, 9999999999)}',
                    'publication_year': random.randint(1950, 2023),
                    'pages': random.randint(100, 800),
                    'total_copies': random.randint(1, 10),
                    'available_copies': random.randint(0, 5),
                    'language': 'en',
                    'format': random.choice(['hardcover', 'paperback', 'ebook']),
                    'location': f'Shelf {chr(65 + i % 26)}-{random.randint(1, 20)}',
                }
            )
            
            # Add authors to the book
            if created:
                # Add 1-3 random authors to each book
                book_authors = random.sample(authors, random.randint(1, min(3, len(authors))))
                book.authors.set(book_authors)
                self.stdout.write(f'  Created book: {book.title}')
            
            books.append(book)
        
        return books

    def create_activity_logs(self, users, books):
        """Create sample activity logs"""
        activity_types = [
            'login', 'logout', 'book_search', 'book_view', 
            'book_borrow', 'book_return', 'profile_update'
        ]
        
        # Create logs for the past 30 days
        for _ in range(100):
            user = random.choice(users)
            activity_type = random.choice(activity_types)
            
            # Create realistic activity based on type
            if activity_type in ['book_view', 'book_borrow', 'book_return']:
                book = random.choice(books)
                object_type = 'book'
                # Convert UUID to string for object_id field
                object_id = str(book.id)
                description = f'User {activity_type.replace("_", " ")} book: {book.title}'
                
                # Store book info in metadata instead of object_id
                metadata = {
                    'book_id': str(book.id),
                    'book_title': book.title,
                    'book_isbn': book.isbn
                }
            else:
                object_type = ''
                object_id = None
                description = f'User {activity_type.replace("_", " ")}'
                metadata = {}
            
            ActivityLog.objects.create(
                user=user,
                activity_type=activity_type,
                description=description,
                object_type=object_type,
                object_id=None,  # Don't use object_id for UUID fields
                metadata=metadata,
                ip_address=fake.ipv4(),
                timestamp=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone())
            )

    def create_book_popularity(self, books):
        """Create book popularity data"""
        for book in books:
            BookPopularity.objects.create(
                book=book,
                total_views=random.randint(10, 500),
                daily_views=random.randint(0, 20),
                weekly_views=random.randint(5, 100),
                monthly_views=random.randint(20, 300),
                total_borrows=random.randint(1, 50),
                monthly_borrows=random.randint(0, 10),
                yearly_borrows=random.randint(5, 40),
                search_appearances=random.randint(5, 100),
                search_clicks=random.randint(1, 50),
                average_rating=round(random.uniform(3.0, 5.0), 1),
                total_ratings=random.randint(1, 20),
                total_reservations=random.randint(0, 15),
                current_reservations=random.randint(0, 3),
                last_viewed=fake.date_time_between(start_date='-7d', end_date='now', tzinfo=timezone.get_current_timezone()),
                last_borrowed=fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.get_current_timezone())
            )

    def create_system_statistics(self):
        """Create system statistics for the past 7 days"""
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            
            SystemStatistics.objects.create(
                date=date,
                total_users=User.objects.count() - i,
                active_users=random.randint(5, 15),
                new_users=random.randint(0, 3),
                total_books=Book.objects.count(),
                available_books=random.randint(10, 20),
                borrowed_books=random.randint(5, 15),
                total_loans=random.randint(0, 5),
                total_returns=random.randint(0, 3),
                total_reservations=random.randint(0, 2),
                total_searches=random.randint(10, 50),
                unique_search_terms=random.randint(5, 25),
                total_fines_collected=random.uniform(0, 50000),
                outstanding_fines=random.uniform(0, 25000),
                average_response_time=random.uniform(100, 300),
                error_rate=random.uniform(0, 2)
            ) 