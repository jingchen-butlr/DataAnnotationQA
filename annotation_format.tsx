// Enhanced annotation interface
interface EnhancedAnnotation {
  id: string;
  // YOLO bbox format
  centerX: number;    // Normalized 0-1
  centerY: number;    // Normalized 0-1
  width: number;      // Normalized 0-1
  height: number;     // Normalized 0-1
  // Enhanced fields
  category: string;
  subcategory: string;  // Flattened with "-" separator (e.g., "lower position-bending")
  attribute_obscured: string | null;     // "0%", "25%", "50%", "75%" for person/furniture/object, null for others
  attribute_heat_residual: string | null; // "yes", "no" for furniture/object, null for person
  object_id: number;
}

// Frame data with timestamp
interface FrameData {
  imageData: ImageData;
  timestamp: number;  // Unix timestamp in seconds
}

// Output format
interface FrameAnnotationOutput {
  data_id: string;
  annotator_id: string;
  annotation_time: number;
  data_time: number;
  annotations: Array<{
    bbox: [number, number, number, number];
    category: string;
    subcategory: string;  // Flattened format
    attribute_obscured: string | null;
    attribute_heat_residual: string | null;
    object_id: number;
  }>;
}

// Category hierarchy - flattened with "-" separator
interface CategoryDef {
  name: string;
  subcategories: string[];
  hasObscured: boolean;
  hasHeatResidual: boolean;
}

const CATEGORY_HIERARCHY: Record<string, CategoryDef> = {
  person: {
    name: 'person',
    subcategories: [
      'sitting',
      'standing',
      'walking',
      'lying down-lying with risk',
      'lying down-lying on the bed/couch',
      'leaning',
      'transition-normal transition',
      'transition-lying with risk transition',
      'transition-lying on the bed transition',
      'lower position-other',
      'lower position-kneeling',
      'lower position-bending',
      'lower position-crouching',
      'other'
    ],
    hasObscured: true,
    hasHeatResidual: false
  },
  furniture: {
    name: 'furniture',
    subcategories: ['bed', 'chair', 'couch', 'table', 'other'],
    hasObscured: true,
    hasHeatResidual: true
  },
  object: {
    name: 'object',
    subcategories: ['pillow', 'laptop', 'monitor', 'water kettle', 'cellphone', 'cup', 'cold object', 'other'],
    hasObscured: true,
    hasHeatResidual: true
  },
  building: {
    name: 'building',
    subcategories: ['window', 'door', 'other'],
    hasObscured: false,
    hasHeatResidual: false
  },
  environment: {
    name: 'environment',
    subcategories: ['sunlight', 'hot heat from the door/window', 'cold heat from the door/window', 
                   'environmental temp change due to the appliance', 'other'],
    hasObscured: false,
    hasHeatResidual: false
  },
  appliance: {
    name: 'appliance',
    subcategories: ['fridge', 'oven', 'heater', 'AC', 'other'],
    hasObscured: false,
    hasHeatResidual: false
  }
};
