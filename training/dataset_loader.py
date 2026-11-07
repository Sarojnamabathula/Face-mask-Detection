import os
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

def get_data_loaders(data_dir: str, batch_size: int = 32, img_size: int = 224):
    """
    Creates PyTorch DataLoaders for train and validation sets with augmentation.
    """
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'val')

    # Data Augmentation for training
    train_transforms = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # Standard transforms for validation
    val_transforms = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # Check if directories exist (fail gracefully with informative message)
    if not os.path.exists(train_dir) or not os.path.exists(val_dir):
        print(f"Error: Could not find train/val directories inside {data_dir}.")
        print("Please ensure your dataset is structured like this:")
        print(f"  {data_dir}/")
        print("    ├── train/")
        print("    │   ├── Mask/")
        print("    │   ├── No Mask/")
        print("    │   └── Incorrect Mask/")
        print("    └── val/")
        print("        ├── Mask/")
        print("        ├── No Mask/")
        print("        └── Incorrect Mask/")
        return None, None, None

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transforms)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transforms)

    # On Windows, num_workers > 0 in DataLoaders can lead to process spawning issues
    workers = 0 if os.name == 'nt' else 2

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=workers)

    return train_loader, val_loader, train_dataset.classes
