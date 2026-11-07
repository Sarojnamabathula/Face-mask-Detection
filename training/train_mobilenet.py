import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models
from torch.optim.lr_scheduler import ReduceLROnPlateau
try:
    from training.dataset_loader import get_data_loaders
except ImportError:
    from dataset_loader import get_data_loaders
import argparse
from tqdm import tqdm

DEFAULT_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset"))
DEFAULT_SAVE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

def get_model(num_classes: int):
    """
    Loads a pre-trained MobileNetV2 and modifies the head for our classes.
    """
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
    
    # Freeze early layers
    for param in model.features[:-4].parameters():
        param.requires_grad = False
        
    # Modify classifier
    model.classifier[1] = nn.Sequential(
        nn.Dropout(p=0.4),
        nn.Linear(model.last_channel, num_classes)
    )
    
    return model

def train_model(data_dir: str, epochs: int, batch_size: int, learning_rate: float, save_dir: str):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_loader, val_loader, class_names = get_data_loaders(data_dir, batch_size=batch_size)
    if train_loader is None:
        return

    num_classes = len(class_names)
    print(f"Found {num_classes} classes: {class_names}")

    model = get_model(num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=2, verbose=True)

    os.makedirs(save_dir, exist_ok=True)
    best_acc = 0.0

    print("Starting training loop...")
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs}")
        print("-" * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
                dataloader = train_loader
            else:
                model.eval()
                dataloader = val_loader

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data
            for inputs, labels in tqdm(dataloader, desc=f"{phase.capitalize()} Phase"):
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(dataloader.dataset)
            epoch_acc = running_corrects.double() / len(dataloader.dataset)

            print(f"{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")

            if phase == 'val':
                scheduler.step(epoch_acc)
                if epoch_acc > best_acc or best_acc == 0.0:
                    best_acc = epoch_acc
                    best_model_path = os.path.join(save_dir, 'best_mobilenetv2_fmd.pth')
                    torch.save({
                        'state_dict': model.state_dict(),
                        'classes': class_names,
                        'accuracy': float(best_acc)
                    }, best_model_path)
                    print(f"New best model saved to {best_model_path} with accuracy {best_acc:.4f}")

    print(f"Training complete. Best val Acc: {best_acc:4f}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train MobileNetV2 on Face Mask Dataset")
    parser.add_argument('--data_dir', type=str, default=DEFAULT_DATA_DIR, help='Path to dataset directory containing train/ and val/ folders')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs to train')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--save_dir', type=str, default=DEFAULT_SAVE_DIR, help='Directory to save the best model weights')
    
    args = parser.parse_args()
    
    train_model(args.data_dir, args.epochs, args.batch_size, args.lr, args.save_dir)
