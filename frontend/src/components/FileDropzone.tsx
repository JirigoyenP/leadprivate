import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  isLoading?: boolean;
}

export default function FileDropzone({ onFileSelect, isLoading }: FileDropzoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    disabled: isLoading,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-gray-300 hover:border-indigo-400'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input {...getInputProps()} />
      <Upload className="mx-auto h-12 w-12 text-gray-400" />
      <p className="mt-2 text-sm text-gray-600">
        {isDragActive
          ? 'Drop the CSV file here...'
          : 'Drag & drop a CSV file here, or click to select'}
      </p>
      <p className="mt-1 text-xs text-gray-500">CSV files with an email column</p>
    </div>
  );
}
