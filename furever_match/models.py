from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from typing_extensions import TypedDict

class DogProfile(BaseModel):
    name: str = Field(description="Name of the dog")
    breed: str = Field(description="Breed of the dog, e.g., 'Mixed', 'Labrador'")
    age_group: str = Field(description="Age category, e.g., 'puppy', 'adult', 'senior'")
    is_neutralized: bool = Field(description="True if the dog is spayed/neutered")
    cat_friendly: bool = Field(description="True if the dog is friendly or compatible with cats")
    
    # Using a 1-5 scale for scoring simplicity
    energy_level: int = Field(ge=1, le=5, description="Energy level of the dog on a scale from 1 (lowest) to 5 (highest)")
    size: int = Field(ge=1, le=5, description="Size of the dog on a scale from 1 (smallest) to 5 (largest)")
    
    # Generic compatibility dictionary, e.g., {"kids": 4, "apartment": 3, "other_dogs": 5}
    compatibility_score: Dict[str, int] = Field(
        default_factory=dict, 
        description="Dictionary mapping compatibility categories (like 'kids', 'apartment') to a score (e.g., 1-5)"
    )

class UserPreferences(BaseModel):
    has_cat: bool = Field(default=False, description="Whether the user currently has a cat")

    # Preferences to match against dog's traits
    ideal_energy_level: int = Field(ge=1, le=5, description="Preferred energy level from 1-5")
    ideal_size: int = Field(ge=1, le=5, description="Preferred dog size from 1-5")


class RawDogData(TypedDict, total=False):
    """Raw extraction output, ready for db_ingestion.transform_dog."""
    name: Optional[str]
    breed: Optional[str]
    age: Optional[str]
    size: Optional[str]           # "small" | "medium" | "large"
    gender: Optional[str]         # "male" | "female"
    description: Optional[str]
    location: Optional[str]
    get_along_with_cats: Optional[bool]
    get_along_with_dogs: Optional[bool]
    get_along_with_kids: Optional[bool]
    scared_of: Optional[str]
    happy_to: Optional[str]
    level_of_training: Optional[str]  # "low" | "medium" | "high"
    source: str
    external_id: str
    images: List[str]
