import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from doctors.models import Doctor

User = get_user_model()
logger = logging.getLogger(__name__)

DOCTORS_DATA = [
    {
        "first_name": "Sarah",
        "last_name": "Williams",
        "email": "sarah.williams@medbook.local",
        "specialisation": "CARDIO",
        "bio": "Expert in adult cardiology with over 15 years of clinical experience. Specializes in preventive cardiology and heart failure management. Graduated from Johns Hopkins University.",
        "years_of_experience": 15,
        "consultation_fee": 150.00,
        "availability": {
            "monday": True,
            "tuesday": True,
            "wednesday": True,
            "thursday": False,
            "friday": True,
        }
    },
    {
        "first_name": "Michael",
        "last_name": "Chen",
        "email": "michael.chen@medbook.local",
        "specialisation": "NEURO",
        "bio": "Board-certified neurologist focusing on stroke prevention, migraines, and neurodegenerative disorders. Dedicated to providing patient-centered care using the latest therapeutic approaches.",
        "years_of_experience": 12,
        "consultation_fee": 180.00,
        "availability": {
            "monday": True,
            "tuesday": False,
            "wednesday": True,
            "thursday": True,
            "friday": False,
        }
    },
    {
        "first_name": "Emily",
        "last_name": "Rodriguez",
        "email": "emily.rodriguez@medbook.local",
        "specialisation": "PEDIA",
        "bio": "Compassionate pediatrician committed to the holistic health of children from infancy through adolescence. Strong advocate for early childhood vaccination and nutrition.",
        "years_of_experience": 8,
        "consultation_fee": 100.00,
        "availability": {
            "monday": True,
            "tuesday": True,
            "wednesday": True,
            "thursday": True,
            "friday": True,
        }
    },
    {
        "first_name": "James",
        "last_name": "Anderson",
        "email": "james.anderson@medbook.local",
        "specialisation": "ORTHO",
        "bio": "Orthopedic surgeon specializing in sports injuries and joint replacements. Works closely with physical therapists to ensure full recovery and mobility for athletes and seniors alike.",
        "years_of_experience": 20,
        "consultation_fee": 200.00,
        "availability": {
            "monday": False,
            "tuesday": True,
            "wednesday": False,
            "thursday": True,
            "friday": True,
        }
    },
    {
        "first_name": "Aisha",
        "last_name": "Patel",
        "email": "aisha.patel@medbook.local",
        "specialisation": "DERM",
        "bio": "Dermatologist with expertise in medical and cosmetic dermatology. Experienced in treating chronic skin conditions like psoriasis and eczema, as well as early skin cancer detection.",
        "years_of_experience": 10,
        "consultation_fee": 130.00,
        "availability": {
            "monday": True,
            "tuesday": True,
            "wednesday": False,
            "thursday": True,
            "friday": False,
        }
    },
    {
        "first_name": "David",
        "last_name": "Kim",
        "email": "david.kim@medbook.local",
        "specialisation": "GP",
        "bio": "Experienced General Practitioner providing comprehensive primary care. Believes in building long-term relationships with families to manage overall well-being and chronic diseases.",
        "years_of_experience": 25,
        "consultation_fee": 80.00,
        "availability": {
            "monday": True,
            "tuesday": True,
            "wednesday": True,
            "thursday": True,
            "friday": True,
        }
    }
]


class Command(BaseCommand):
    help = "Seeds the database with realistic doctor profiles."

    def handle(self, *args, **options):
        self.stdout.write("Starting doctor seeding process...")
        
        created_count = 0
        updated_count = 0

        for doc_data in DOCTORS_DATA:
            # Create or get user
            username = f"{doc_data['first_name'].lower()}.{doc_data['last_name'].lower()}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": doc_data["first_name"],
                    "last_name": doc_data["last_name"],
                    "email": doc_data["email"],
                    "role": User.Role.DOCTOR,
                }
            )

            if created:
                user.set_password("MedBook123!")
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created User: {user.username}"))
            else:
                self.stdout.write(f"User already exists: {user.username}")

            # Create or update Doctor profile
            doctor, doc_created = Doctor.objects.update_or_create(
                user=user,
                defaults={
                    "specialisation": doc_data["specialisation"],
                    "bio": doc_data["bio"],
                    "years_of_experience": doc_data["years_of_experience"],
                    "consultation_fee": doc_data["consultation_fee"],
                    "available_monday": doc_data["availability"]["monday"],
                    "available_tuesday": doc_data["availability"]["tuesday"],
                    "available_wednesday": doc_data["availability"]["wednesday"],
                    "available_thursday": doc_data["availability"]["thursday"],
                    "available_friday": doc_data["availability"]["friday"],
                }
            )

            if doc_created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  -> Created Doctor Profile for {user.username}"))
            else:
                updated_count += 1
                self.stdout.write(f"  -> Updated Doctor Profile for {user.username}")

        self.stdout.write(self.style.SUCCESS(f"Seeding complete! Created: {created_count}, Updated: {updated_count}"))
