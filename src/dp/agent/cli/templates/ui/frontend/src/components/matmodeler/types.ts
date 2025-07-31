export enum MaterialMode {
    CreateAtom,
    Selection,
    Measure,
}

export enum MeasureType {
    Distance = 'Distance',
    Angle = 'Angle',
    Dihedral = 'Dihedral',
}

export interface ASEAtom {
    cart_coord: number[];
    formula: string;
    frac_coord: number[];
    id?: number;
    move_flag?: boolean[];
}

export interface ASEDataItem {
    atoms: ASEAtom[];
    angle?: number[];
    length?: number[];
    matrix?: number[][];
    spacegroup?: [number, string];
    chemical_formula?: string;
}

export interface SpaceGroup {
    symbol: string;
    no: number;
}

export interface LatticeValue {
    a: number;
    b: number;
    c: number;
    alpha: number;
    beta: number;
    gamma: number;
}

export interface LatticeParams extends LatticeValue {
    matrix?: number[][];
    spacegroup: SpaceGroup;
}

export interface Lattice extends LatticeParams {
    vecA: number[];
    vecB: number[];
    vecC: number[];
    // center: number[]
    matrix: number[][];
    invertMatrix: number[][];
    volume: number;
}

export interface AtomParams {
    element: string;
    xyz?: number[];
    abc?: number[];
    id?: number;
    moveFlag?: boolean[];
}

export interface Atom {
    order?: number;
    symmetry?: number[];
    element: string;
    xyz: number[];
    abc?: number[];
    moveFlag?: boolean[];
    id?: number;
}

export interface MaterialItem {
    expand: number[];
    atoms: Atom[];
    lattice?: Lattice;
    chemicalFormula?: string;
}

export interface MaterialCleaveParams {
    h: number;
    k: number;
    l: number;
    depth: number;
}

export interface MaterialCleave extends MaterialCleaveParams {
    depth: number;
}

export interface Ligand {
    element: string;
    color: string;
}
