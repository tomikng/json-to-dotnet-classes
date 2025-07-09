#!/usr/bin/env python3
"""
JSON to C# Class Generator
A configurable tool that generates C# classes with JsonPropertyName attributes from JSON structure.
Each class is saved to a separate file.

Usage:
    python json_to_csharp.py input.json
    python json_to_csharp.py input.json --output Generated --namespace MyApp.Models --root-class MyDto
"""

import json
import os
import re
import argparse
from typing import Dict, Any, Set
from pathlib import Path
import inflect

class CSharpClassGenerator:
    def __init__(self, json_file_path: str, output_dir: str = "Generated", 
                 namespace: str = "Generated.Models", root_class_name: str = "RootDto",
                 use_records: bool = False):
        self.json_file_path = json_file_path
        self.output_dir = output_dir
        self.namespace = namespace
        self.root_class_name = root_class_name
        self.use_records = use_records
        self.processed_classes: Set[str] = set()
        self.class_definitions: Dict[str, Dict] = {}
        self.inflect_engine = inflect.engine()
        
        Path(self.output_dir).mkdir(exist_ok=True)
    
    def json_type_to_csharp_type(self, value: Any, property_name: str = "") -> str:
        if value is None:
            return "object?"
        elif isinstance(value, bool):
            return "bool?"
        elif isinstance(value, int):
            return "int?"
        elif isinstance(value, float):
            return "decimal?"
        elif isinstance(value, str):
            # Check if it looks like a DateTime
            if self.is_datetime_string(value):
                return "DateTime?"
            return "string?"
        elif isinstance(value, list):
            if len(value) == 0:
                return "List<object>?"
            # Analyze the first item to determine list type
            first_item = value[0]
            if isinstance(first_item, dict):
                class_name = self.get_class_name_from_context(property_name, is_array=True)
                return f"List<{class_name}>?"
            else:
                item_type = self.json_type_to_csharp_type(first_item).rstrip('?')
                return f"List<{item_type}>?"
        elif isinstance(value, dict):
            class_name = self.get_class_name_from_context(property_name)
            return f"{class_name}?"
        else:
            return "object?"
    
    def is_datetime_string(self, value: str) -> bool:
        """Check if string looks like a DateTime."""
        datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{4}-\d{2}-\d{2}',  # Date only
        ]
        return any(re.search(pattern, value) for pattern in datetime_patterns)
    
    def get_class_name_from_context(self, property_name: str, is_array: bool = False) -> str:
        """Generate appropriate class name from property name."""
        if not property_name:
            return "GeneratedClass"
        
        # Remove common suffixes/prefixes
        class_name = property_name
        
        # Handle array naming with proper singularization
        if is_array:
            # Use inflect to properly singularize
            singular = self.inflect_engine.singular_noun(class_name)  # type: ignore
            if singular:
                class_name = singular
        
        # Handle common patterns
        if class_name.endswith('DD'):
            class_name = class_name[:-2] + "Type"
        elif class_name.startswith('str'):
            class_name = class_name[3:]
        
        class_name = self.to_pascal_case(class_name)
        
        return class_name if class_name else "GeneratedClass"
    
    def to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        if not text:
            return "GeneratedClass"
        
        # Handle camelCase and snake_case
        words = re.findall(r'[A-Z][a-z]*|[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', text)
        if not words:
            words = [text]
        
        return ''.join(word.capitalize() for word in words)
    
    def analyze_object(self, obj: Dict[str, Any], class_name: str = "") -> Dict[str, str]:
        """Analyze an object and return property definitions."""
        properties = {}
        
        for key, value in obj.items():
            csharp_type = self.json_type_to_csharp_type(value, key)
            properties[key] = csharp_type
            
            # If it's a nested object, analyze it recursively
            if isinstance(value, dict):
                nested_class_name = self.get_class_name_from_context(key)
                if nested_class_name not in self.processed_classes:
                    self.class_definitions[nested_class_name] = self.analyze_object(value, nested_class_name)
                    self.processed_classes.add(nested_class_name)
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                nested_class_name = self.get_class_name_from_context(key, is_array=True)
                if nested_class_name not in self.processed_classes:
                    self.class_definitions[nested_class_name] = self.analyze_object(value[0], nested_class_name)
                    self.processed_classes.add(nested_class_name)
        
        return properties
    
    def generate_class_content(self, class_name: str, properties: Dict[str, str]) -> str:
        """Generate C# class content."""
        usings = [
            "using System.Text.Json.Serialization;",
            "using System;",
            "using System.Collections.Generic;"
        ]
        
        class_content = []
        class_content.extend(usings)
        class_content.append("")
        class_content.append(f"namespace {self.namespace};")
        class_content.append("")
        
        class_type = "record" if self.use_records else "class"
        class_content.append(f"public {class_type} {class_name}")
        class_content.append("{")
        
        for json_property, csharp_type in properties.items():
            class_content.append(f"    [JsonPropertyName(\"{json_property}\")]")
            
            property_name = self.to_pascal_case(json_property)
            if property_name == json_property:
                property_name = json_property
            
            class_content.append(f"    public {csharp_type} {property_name} {{ get; init; }}")
            class_content.append("")
        
        class_content.append("}")
        
        return "\n".join(class_content)
    
    def save_class_to_file(self, class_name: str, content: str):
        """Save class content to file."""
        file_path = Path(self.output_dir) / f"{class_name}.cs"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {file_path}")
    
    def generate_classes(self):
        """Main method to generate all classes."""
        print(f"Reading JSON file: {self.json_file_path}")
        
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("Analyzing JSON structure...")
        
        if isinstance(data, dict):
            root_properties = self.analyze_object(data, "RootObject")
            self.class_definitions[self.root_class_name] = root_properties
        elif isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict):
                item_class_name = f"{self.root_class_name}Item"
                root_properties = self.analyze_object(first_item, item_class_name)
                self.class_definitions[self.root_class_name] = {"Items": f"List<{item_class_name}>?"}
                self.class_definitions[item_class_name] = root_properties
        
        print(f"Found {len(self.class_definitions)} classes to generate")
        
        # Generate all class files
        for class_name, properties in self.class_definitions.items():
            content = self.generate_class_content(class_name, properties)
            self.save_class_to_file(class_name, content)
        
        print(f"\nAll classes generated in '{self.output_dir}' directory!")
        print(f"Total files created: {len(self.class_definitions)}")
        print(f"Namespace: {self.namespace}")
        print(f"Root class: {self.root_class_name}")

def main():
    parser = argparse.ArgumentParser(
        description="Generate C# classes from JSON structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json
  %(prog)s data.json --output Models --namespace MyApp.Models
  %(prog)s data.json --root-class ApiResponse --records
        """
    )
    
    parser.add_argument('json_file', help='Path to the JSON file to process')
    parser.add_argument('-o', '--output', default='Generated', 
                      help='Output directory for generated files (default: Generated)')
    parser.add_argument('-n', '--namespace', default='Generated.Models',
                      help='C# namespace for generated classes (default: Generated.Models)')
    parser.add_argument('-r', '--root-class', default='RootDto',
                      help='Name of the root class (default: RootDto)')
    parser.add_argument('--records', action='store_true',
                      help='Generate records instead of classes')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"Error: JSON file '{args.json_file}' not found!")
        return 1
    
    print("JSON to C# Class Generator")
    print("=" * 50)
    print(f"Input file: {args.json_file}")
    print(f"Output directory: {args.output}")
    print(f"Namespace: {args.namespace}")
    print(f"Root class: {args.root_class}")
    print(f"Type: {'records' if args.records else 'classes'}")
    print()
    
    generator = CSharpClassGenerator(
        json_file_path=args.json_file,
        output_dir=args.output,
        namespace=args.namespace,
        root_class_name=args.root_class,
        use_records=args.records
    )
    
    try:
        generator.generate_classes()
        print("\n✅ Done! You can now use these classes in your C# project.")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 