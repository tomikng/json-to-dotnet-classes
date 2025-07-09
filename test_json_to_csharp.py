#!/usr/bin/env python3
"""
Unit tests for JSON to C# Class Generator
Tests all major functionality including type detection, naming conventions, and generation.
"""

import unittest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from json_to_csharp import CSharpClassGenerator

class TestCSharpClassGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_json_file = os.path.join(self.temp_dir, "test.json")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def write_test_json(self, data):
        """Helper method to write test JSON data."""
        with open(self.test_json_file, 'w') as f:
            json.dump(data, f)
    
    def test_json_type_to_csharp_type_basic_types(self):
        """Test basic type conversion from JSON to C#."""
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        
        # Test basic types
        self.assertEqual(generator.json_type_to_csharp_type(None), "object?")
        self.assertEqual(generator.json_type_to_csharp_type(True), "bool?")
        self.assertEqual(generator.json_type_to_csharp_type(42), "int?")
        self.assertEqual(generator.json_type_to_csharp_type(3.14), "decimal?")
        self.assertEqual(generator.json_type_to_csharp_type("hello"), "string?")
        
    def test_datetime_detection(self):
        """Test DateTime string detection."""
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        
        # ISO date formats
        self.assertTrue(generator.is_datetime_string("2023-01-15T10:30:00Z"))
        self.assertTrue(generator.is_datetime_string("2023-01-15T10:30:00.123"))
        self.assertTrue(generator.is_datetime_string("2023-01-15"))
        
        # Non-date strings
        self.assertFalse(generator.is_datetime_string("hello world"))
        self.assertFalse(generator.is_datetime_string("123-456-789"))
        
        # DateTime type conversion
        self.assertEqual(generator.json_type_to_csharp_type("2023-01-15T10:30:00Z"), "DateTime?")
        
    def test_array_type_detection(self):
        """Test array type detection and class naming."""
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        
        # Empty array
        self.assertEqual(generator.json_type_to_csharp_type([]), "List<object>?")
        
        # Array of primitives
        self.assertEqual(generator.json_type_to_csharp_type([1, 2, 3]), "List<int>?")
        self.assertEqual(generator.json_type_to_csharp_type(["a", "b"]), "List<string>?")
        
        # Array of objects
        result = generator.json_type_to_csharp_type([{"id": 1}], "Users")
        self.assertEqual(result, "List<User>?")
    
    def test_pluralization_with_inflect(self):
        """Test proper pluralization using inflect library."""
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        
        # Test common pluralization cases
        self.assertEqual(generator.get_class_name_from_context("Activities", is_array=True), "Activity")
        self.assertEqual(generator.get_class_name_from_context("Categories", is_array=True), "Category")
        self.assertEqual(generator.get_class_name_from_context("Users", is_array=True), "User")
        self.assertEqual(generator.get_class_name_from_context("Companies", is_array=True), "Company")
        
    def test_pascal_case_conversion(self):
        """Test PascalCase conversion."""
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        
        self.assertEqual(generator.to_pascal_case("user_name"), "UserName")
        self.assertEqual(generator.to_pascal_case("firstName"), "FirstName")
        self.assertEqual(generator.to_pascal_case("API_KEY"), "APIKEY")  # Current behavior
        self.assertEqual(generator.to_pascal_case("simple"), "Simple")
        
    def test_special_naming_conventions(self):
        """Test special naming conventions (DD suffix, str prefix)."""
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        
        # DD suffix handling
        self.assertEqual(generator.get_class_name_from_context("StatusDD"), "StatusType")
        self.assertEqual(generator.get_class_name_from_context("TypeDD"), "TypeType")
        
        # str prefix handling
        self.assertEqual(generator.get_class_name_from_context("strStatus"), "Status")
        self.assertEqual(generator.get_class_name_from_context("strUserName"), "UserName")
    
    def test_simple_object_generation(self):
        """Test generation of simple objects."""
        test_data = {
            "id": 1,
            "name": "Test User",
            "isActive": True,
            "createdAt": "2023-01-15T10:30:00Z"
        }
        
        self.write_test_json(test_data)
        generator = CSharpClassGenerator(
            self.test_json_file, 
            self.output_dir,
            namespace="Test.Models",
            root_class_name="TestDto"
        )
        
        generator.generate_classes()
        
        # Check that file was generated
        expected_file = Path(self.output_dir) / "TestDto.cs"
        self.assertTrue(expected_file.exists())
        
        # Check file content
        content = expected_file.read_text()
        self.assertIn("namespace Test.Models;", content)
        self.assertIn("public class TestDto", content)
        self.assertIn('[JsonPropertyName("id")]', content)
        self.assertIn("public int? Id { get; init; }", content)
        self.assertIn('[JsonPropertyName("name")]', content)
        self.assertIn("public string? Name { get; init; }", content)
        self.assertIn('[JsonPropertyName("isActive")]', content)
        self.assertIn("public bool? IsActive { get; init; }", content)
        self.assertIn('[JsonPropertyName("createdAt")]', content)
        self.assertIn("public DateTime? CreatedAt { get; init; }", content)
        
        # Check auto-generated comment
        self.assertIn("// <auto-generated>", content)
        self.assertIn("// This code was generated by the JSON to C# Class Generator", content)
        self.assertIn("// Source: https://github.com/tomikng/json-to-dotnet-classes", content)
    
    def test_nested_objects_generation(self):
        """Test generation with nested objects."""
        test_data = {
            "user": {
                "id": 1,
                "name": "John",
                "profile": {
                    "age": 30,
                    "city": "NYC"
                }
            }
        }
        
        self.write_test_json(test_data)
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        generator.generate_classes()
        
        # Check multiple files were generated
        root_file = Path(self.output_dir) / "RootDto.cs"
        user_file = Path(self.output_dir) / "User.cs"
        profile_file = Path(self.output_dir) / "Profile.cs"
        
        self.assertTrue(root_file.exists())
        self.assertTrue(user_file.exists())
        self.assertTrue(profile_file.exists())
        
        # Check nested references
        root_content = root_file.read_text()
        self.assertIn("public User? User { get; init; }", root_content)
        
        user_content = user_file.read_text()
        self.assertIn("public Profile? Profile { get; init; }", user_content)
    
    def test_arrays_generation(self):
        """Test generation with arrays."""
        test_data = {
            "users": [
                {
                    "id": 1,
                    "name": "John"
                }
            ],
            "tags": ["tag1", "tag2"]
        }
        
        self.write_test_json(test_data)
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        generator.generate_classes()
        
        # Check files
        root_file = Path(self.output_dir) / "RootDto.cs"
        user_file = Path(self.output_dir) / "User.cs"
        
        self.assertTrue(root_file.exists())
        self.assertTrue(user_file.exists())
        
        # Check array types
        root_content = root_file.read_text()
        self.assertIn("public List<User>? Users { get; init; }", root_content)
        self.assertIn("public List<string>? Tags { get; init; }", root_content)
    
    def test_records_vs_classes(self):
        """Test generation of records vs classes."""
        test_data = {"id": 1, "name": "test"}
        self.write_test_json(test_data)
        
        # Test class generation (default)
        generator_class = CSharpClassGenerator(
            self.test_json_file, 
            self.output_dir + "_class",
            use_records=False
        )
        generator_class.generate_classes()
        
        # Test record generation
        generator_record = CSharpClassGenerator(
            self.test_json_file, 
            self.output_dir + "_record",
            use_records=True
        )
        generator_record.generate_classes()
        
        # Check class
        class_file = Path(self.output_dir + "_class") / "RootDto.cs"
        class_content = class_file.read_text()
        self.assertIn("public class RootDto", class_content)
        
        # Check record
        record_file = Path(self.output_dir + "_record") / "RootDto.cs"
        record_content = record_file.read_text()
        self.assertIn("public record RootDto", record_content)
    
    def test_empty_json_handling(self):
        """Test handling of empty JSON objects."""
        self.write_test_json({})
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        generator.generate_classes()
        
        # Should still generate a file
        root_file = Path(self.output_dir) / "RootDto.cs"
        self.assertTrue(root_file.exists())
    
    def test_array_root_handling(self):
        """Test handling when JSON root is an array."""
        test_data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ]
        
        self.write_test_json(test_data)
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        generator.generate_classes()
        
        # Should generate root class and item class
        root_file = Path(self.output_dir) / "RootDto.cs"
        item_file = Path(self.output_dir) / "RootDtoItem.cs"
        
        self.assertTrue(root_file.exists())
        self.assertTrue(item_file.exists())
        
        # Check root contains list
        root_content = root_file.read_text()
        self.assertIn("public List<RootDtoItem>? Items { get; init; }", root_content)
    
    def test_analyze_object_properties(self):
        """Test the analyze_object method."""
        generator = CSharpClassGenerator(self.test_json_file, self.output_dir)
        
        test_obj = {
            "stringProp": "test",
            "intProp": 42,
            "boolProp": True,
            "dateProp": "2023-01-15T10:30:00Z",
            "arrayProp": [1, 2, 3],
            "nestedProp": {"inner": "value"}
        }
        
        properties = generator.analyze_object(test_obj)
        
        self.assertEqual(properties["stringProp"], "string?")
        self.assertEqual(properties["intProp"], "int?")
        self.assertEqual(properties["boolProp"], "bool?")
        self.assertEqual(properties["dateProp"], "DateTime?")
        self.assertEqual(properties["arrayProp"], "List<int>?")
        self.assertEqual(properties["nestedProp"], "NestedProp?")

class TestCLIInterface(unittest.TestCase):
    """Test the command line interface."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_json_file = os.path.join(self.temp_dir, "test.json")
        
        # Create a simple test JSON file
        test_data = {"id": 1, "name": "test"}
        with open(self.test_json_file, 'w') as f:
            json.dump(test_data, f)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('sys.argv')
    def test_cli_basic_usage(self, mock_argv):
        """Test basic CLI usage."""
        from json_to_csharp import main
        
        mock_argv.__getitem__.side_effect = lambda i: [
            'json_to_csharp.py',
            self.test_json_file
        ][i]
        mock_argv.__len__.return_value = 2
        
        # Should not raise an exception
        try:
            result = main()
            self.assertEqual(result, 0)  # Success
        except SystemExit as e:
            self.assertEqual(e.code, 0)  # argparse calls sys.exit(0) on success
    
    @patch('sys.argv')
    def test_cli_missing_file(self, mock_argv):
        """Test CLI with missing file."""
        from json_to_csharp import main
        
        mock_argv.__getitem__.side_effect = lambda i: [
            'json_to_csharp.py',
            'nonexistent.json'
        ][i]
        mock_argv.__len__.return_value = 2
        
        result = main()
        self.assertEqual(result, 1)  # Error

class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_json_file = os.path.join(self.temp_dir, "test.json")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON."""
        # Write invalid JSON
        with open(self.test_json_file, 'w') as f:
            f.write('{"invalid": json content}')
        
        generator = CSharpClassGenerator(self.test_json_file, self.temp_dir)
        
        # Should raise an exception for invalid JSON
        with self.assertRaises(json.JSONDecodeError):
            generator.generate_classes()
    
    def test_nonexistent_file_handling(self):
        """Test handling of nonexistent files."""
        generator = CSharpClassGenerator("nonexistent.json", self.temp_dir)
        
        # Should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            generator.generate_classes()

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 