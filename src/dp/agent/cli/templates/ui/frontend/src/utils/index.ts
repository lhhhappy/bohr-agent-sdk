import { Format, VESTA_COLOR_TABLE } from 'dpmol';
import {
    Matrix, add, det, identity, inv, mod, multiply, divide, subtract, norm, dot, acos, sqrt,
    sin,
    cos,
    pi,
    cross,
    matrix,
    transpose,
    abs,
} from 'mathjs';
import { ElementSymbolColors } from 'dpmol';
import { Color } from 'dpmol';
import { StructureElement, StructureProperties } from 'dpmol';
import { Loci } from 'dpmol';
import { MoleculeInfoParam } from 'dpmol';
import { Lattice, Atom, AtomParams, LatticeParams, MaterialItem, ASEDataItem, MaterialCleaveParams } from '../components/matmodeler/types';
import { Bulk } from './bulk';
import { buildBulk, getSurfaceVector } from './cleavage';
import _ from 'lodash-es';

export const getExtByName = (name: string) => {
    const index = name.lastIndexOf('.');
    const hasExt = index > -1;
    // 文件名中包含 POSCAR 或 CONTCAR 的文件（POSCAR、CONTCAR 必须大写）
    if (!hasExt && (name.includes('POSCAR') || name.includes('CONTCAR'))) {
        return 'POSCAR';
    }
    if (!hasExt && name === 'XDATCAR') {
        return 'XDATCAR';
    }

    if (!hasExt && name.includes('STRU')) {
        return 'STRU';
    }
    // if (!hasExt && name === 'XDATCAR') {
    //     return 'dump';
    // }
    // if (name.toLowerCase().startsWith('poscar') || name.toLowerCase().startsWith('contcar')) {
    //     return 'POSCAR';
    // }
    if (name.toLowerCase().startsWith('lammpstrj')) {
        return 'dump';
    }

    if (index === -1) {
        return '';
    }
    const ext = name.substring(index + 1).toLowerCase();
    if (['poscar', 'contcar', 'vasp'].includes(ext)) {
        return 'POSCAR';
    }
    // 移除 lammps、lmp、conf 后缀
    // if (['lammps', 'lmp', 'conf'].includes(ext)) {
    //     return 'dump';
    // }
    // xtc trr为后缀 gro是临时后缀
    // if (ext === 'xtc' || ext === 'trr' || ext === 'gro') {
    //     return 'dump';
    // }
    if (ext.endsWith('lammpstrj')) {
        return 'dump';
    }
    return ext;
};

// TODO: P2 拆分解（分类）、移除废弃方法

const Tolerance = 0.005;

export const CustomFormatMap: {
    [k: string]: Format;
} = {
    dump: Format.Dump,
    gro: Format.Gro,
    xdatcar: Format.VaspXdatcar,
};

export const CustomFormatList = Object.keys(CustomFormatMap);

export function isCustomFormat(format: string) {
    return CustomFormatList.includes(format);
}

export const isMac = /macintosh|mac os x/i.test(navigator.userAgent);

export const MaterialExts = [
    'cif',
    'dump',
    'xyz',
    'POSCAR',
    'mol',
    'mol2',
    'sdf',
    'gro',
    'trr',
    'xtc',
    'STRU',
    'XDATCAR',
    // 'pdb',
];

function unitVector(x: number[]): number[] {
    const y = x.map((n) => n as number) // Ensure elements are numbers
    return divide(y, norm(y)) as number[]
}

export function cellparToCell(
    cellpar: number | number[],
    abNormal: number[] = [0, 0, 1],
    aDirection?: number[]
): number[][] {
    if (!aDirection) {
        const crossProduct = cross(abNormal, [1, 0, 0]) as number[]
        if ((norm(crossProduct) as number) < 1e-5) {
            aDirection = [0, 0, 1]
        } else {
            aDirection = [1, 0, 0]
        }
    }

    const ad = aDirection
    const Z = unitVector(abNormal)
    const X = unitVector(ad.map((v, i) => v - dot(ad, Z) * Z[i]))
    const Y = cross(Z, X) as number[]

    let alpha = 90,
        beta = 90,
        gamma = 90
    let a, b, c

    if (typeof cellpar === 'number') {
        a = b = c = cellpar
    } else if (cellpar.length === 1) {
        a = b = c = cellpar[0]
    } else if (cellpar.length === 3) {
        ;[a, b, c] = cellpar
    } else {
        ;[a, b, c, alpha, beta, gamma] = cellpar
    }

    const eps = 2 * Number.EPSILON // around 1.4e-14

    let cosAlpha = abs(alpha - 90) < eps ? 0 : cos((alpha * pi) / 180)
    let cosBeta = abs(beta - 90) < eps ? 0 : cos((beta * pi) / 180)
    let cosGamma, sinGamma

    if (abs(gamma - 90) < eps) {
        cosGamma = 0
        sinGamma = 1
    } else if (abs(gamma + 90) < eps) {
        cosGamma = 0
        sinGamma = -1
    } else {
        cosGamma = cos((gamma * pi) / 180)
        sinGamma = sin((gamma * pi) / 180)
    }

    const va = [a, 0, 0]
    const vb = [b * cosGamma, b * sinGamma, 0]
    const cx = cosBeta
    const cy = (cosAlpha - cosBeta * cosGamma) / sinGamma
    const czSqr = 1 - cx * cx - cy * cy
    if (czSqr < 0) throw new Error('cz_sqr is negative, which is not possible')
    const cz = sqrt(czSqr) as number

    const vc = [c * cx, c * cy, c * cz]

    const abc = matrix([va, vb, vc])
    const T = matrix([X, Y, Z])
    const cell = multiply(abc, transpose(T))

    return cell.toArray() as number[][]
}

export function cellToCellpar(
    cell: number[][],
    radians: boolean = false
): number[] {
    /**
     * Returns the cell parameters [a, b, c, alpha, beta, gamma].
     *
     * Angles are in degrees unless radians=True is used.
     */

    const lengths = cell.map((v) => norm(v))
    const angles = []

    for (let i = 0; i < 3; i++) {
        const j = (i + 2) % 3
        const k = (i + 1) % 3
        const ll = multiply(lengths[j], lengths[k]) as number
        let angle

        if (ll > 1e-16) {
            const x = dot(cell[j], cell[k]) / ll
            angle = (180.0 / pi) * (acos(x) as number)
        } else {
            angle = 90.0
        }
        angles.push(angle)
    }

    if (radians) {
        for (let i = 0; i < angles.length; i++) {
            angles[i] = (angles[i] * pi) / 180
        }
    }

    return [...(lengths as number[]), ...angles]
}


function combineElements(arr: number[], num = arr.length, combine = [] as number[][]): number[][] {
    if (num === 0) return [];
    if (num === 1) return [...combine, ...arr.map(n => [n])];
    if (arr.length === num) return combineElements(arr, num - 1, [arr.slice()]);
    for (let i = 0; i < arr.length - 1; i++) {
        for (let j = i + 1; j < arr.length; j++) {
            combine.push([arr[i], arr[j]]);
        }
    }
    return combineElements(arr, num - 1, combine);
}

export function isSameVec(source: number[], target: number[]) {
    return source.every((n, i) => n === target[i]);
}

export function isOriginVec(image: number[]) {
    return isSameVec(image, [0, 0, 0]);
}

export function isMaterialFilename(name: string) {
    const ext = getExtByName(name);
    return MaterialExts.includes(ext);
}

export function createOriginalMaterial(params: { lattice?: LatticeParams; atoms: AtomParams[] }): MaterialItem {
    const material: MaterialItem = {
        expand: [1, 1, 1],
        atoms: [],
        lattice: undefined,
    };
    const lattice = params?.lattice ? createLatticeByParams(params?.lattice) : undefined;
    const atoms = params.atoms.map((a, index) => {
        const atom = createAtom(a, {
            lattice,
            order: index,
        });

        return atom;
    });

    material.lattice = lattice;
    material.atoms = atoms;
    return material;
}

export function createSymmetryMaterial(material: MaterialItem): MaterialItem {
    if (!material.lattice) {
        return material;
    }
    const symmetryMaterial = createOriginalMaterial({
        lattice: material.lattice,
        atoms: material.atoms,
    });
    const { atoms } = symmetryMaterial;
    const symmetryAtoms = getSymmetryAtoms(atoms, material.lattice);

    symmetryMaterial.atoms = [...symmetryMaterial.atoms, ...symmetryAtoms];

    return symmetryMaterial;
}

export function getParamsFromSymmetryMaterial(material: MaterialItem): MoleculeInfoParam {
    const elements: string[] = [];
    const xyzs: number[][] = [];
    const moveFlags: boolean[][] = [];
    material.atoms.map(atom => {
        elements.push(atom.element);
        xyzs.push(atom.xyz);
        moveFlags.push(atom.moveFlag || []);
    });

    return {
        elements,
        xyzs,
        lattice: material.lattice,
        moveFlags,
    };
}

export function getMatrix4FormVec3(vec3: number[]) {
    const matrix = (identity(4) as Matrix).toArray() as number[][];
    vec3.forEach((n, idx) => {
        matrix[3][idx] = n;
    });
    return matrix;
}

export function getTransMatrix4FormSymmetryVec(symmetryVec: number[], matrix: number[][]) {
    let transVec3 = [0, 0, 0];
    symmetryVec.forEach((symmetry, idx) => {
        if (!symmetry) {
            return;
        }
        transVec3 = add(transVec3, multiply(matrix[idx], symmetry)) as number[];
    });
    return getMatrix4FormVec3(transVec3);
}

export function transformMatrix4(vec: number[], matrix4: number[][]) {
    const [x, y, z] = vec;
    const w = 1 / (matrix4[0][3] * x + matrix4[1][3] * y + matrix4[2][3] * z + matrix4[3][3] || 1.0);
    const a = (matrix4[0][0] * x + matrix4[1][0] * y + matrix4[2][0] * z + matrix4[3][0]) * w;
    const b = (matrix4[0][1] * x + matrix4[1][1] * y + matrix4[2][1] * z + matrix4[3][1]) * w;
    const c = (matrix4[0][2] * x + matrix4[1][2] * y + matrix4[2][2] * z + matrix4[3][2]) * w;
    return [a, b, c];
}

export function createLatticeByParams(params: LatticeParams): Lattice {
    const { a, b, c, alpha, beta, gamma, spacegroup } = params;
    const matrix = params.matrix || cellparToCell([a, b, c, alpha, beta, gamma]);
    const invertMatrix = inv(matrix);

    const vecA = matrix[0];
    const vecB = matrix[1];
    const vecC = matrix[2];

    const volume = det(matrix);

    return {
        spacegroup,
        a,
        b,
        c,
        volume,
        alpha,
        beta,
        gamma,
        vecA,
        vecB,
        vecC,
        matrix,
        invertMatrix,
    };
}

export function createAtom(
    params: AtomParams,
    extraParams?: {
        order?: number;
        lattice?: Lattice;
        symmetry?: number[];
    }
): Atom {
    const { order, lattice, symmetry } = extraParams || {};
    const { element, id = order ? order + 1 : 0, moveFlag = [true, true, true] } = params;

    if (!params.abc && !params.xyz) {
        throw new Error('createAtom: Need xyz or abc!');
    }

    if (!lattice && !params.xyz) {
        throw new Error('createAtom: Need xyz or lattice!');
    }

    let abc = (() => {
        const { xyz, abc } = params;
        // case1: 非晶体，无abc，无lattice
        if (!lattice) {
            return undefined;
        }

        // case2: 晶体，非对称性，已有xyz，计算abc
        if (!abc) {
            return multiply(xyz!, lattice.invertMatrix) as number[];
        }

        // case3: 晶体，非对称性，已有abc
        if (!symmetry || isOriginVec(symmetry)) {
            return abc;
        }

        // case4: 晶体，有对称性，已有abc，计算对称位置的abc
        const transMatrix4 = getTransMatrix4FormSymmetryVec(symmetry, (identity(3) as Matrix).toArray() as number[][]);
        const symmetryAbc = transformMatrix4(abc, transMatrix4);
        return symmetryAbc;
    })();

    let xyz = (() => {
        const { xyz, abc } = params;
        // case1: 非晶体，无lattice
        if (!lattice) {
            return xyz!;
        }

        // case2: 晶体，非对称性，已有abc，计算xyz
        if (!xyz) {
            return multiply(abc!, lattice.matrix) as number[];
        }

        // case3: 晶体，非对称性，已有xyz
        if (!symmetry || isOriginVec(symmetry)) {
            return xyz;
        }

        // case4: 晶体，有对称性，已有xyz，计算对称位置的xyz
        const transMatrix4 = getTransMatrix4FormSymmetryVec(symmetry, lattice.matrix);
        const symmetryXyz = transformMatrix4(xyz, transMatrix4);
        return symmetryXyz;
    })();

    // 超出晶格坐标，处理回晶格内
    const needRecalculate = abc && abc.some(n => n < 0 || n > 1);
    if (needRecalculate) {
        abc = mod(abc!, 1);
    }
    if (lattice) {
        xyz = multiply(abc!, lattice!.matrix) as number[];
    }

    return {
        element,
        xyz,
        abc,
        order,
        symmetry,
        id,
        moveFlag,
    };
}

export function getSymmetryAtoms(atoms: Atom[], lattice: Lattice) {
    const symmetryAtoms: Atom[] = [];

    atoms.forEach((atom, idx) => {
        const { abc } = atom;
        if (!abc || abc[0] === undefined) return;

        {
            const zeroElements = [];
            if (Math.abs(abc[0]) <= Tolerance) zeroElements.push(0);
            if (Math.abs(abc[1]) <= Tolerance) zeroElements.push(1);
            if (Math.abs(abc[2]) <= Tolerance) zeroElements.push(2);
            const coordPermutations = combineElements(zeroElements);
            const perms = coordPermutations.map(elements => [
                Number(elements.includes(0)),
                Number(elements.includes(1)),
                Number(elements.includes(2)),
            ]);
            perms.forEach(perm => {
                const sAtom = createAtom(atom, {
                    order: idx,
                    lattice,
                    symmetry: perm,
                });
                symmetryAtoms.push(sAtom);
            });
        }

        {
            const oneElements = [];
            if (Math.abs(1 - abc[0]) <= Tolerance) oneElements.push(0);
            if (Math.abs(1 - abc[1]) <= Tolerance) oneElements.push(1);
            if (Math.abs(1 - abc[2]) <= Tolerance) oneElements.push(2);
            const coordPermutations = combineElements(oneElements);
            const perms = coordPermutations.map(elements => [
                -Number(elements.includes(0)),
                -Number(elements.includes(1)),
                -Number(elements.includes(2)),
            ]);
            perms.forEach(perm => {
                const sAtom = createAtom(atom, {
                    order: idx,
                    lattice,
                    symmetry: perm,
                });
                symmetryAtoms.push(sAtom);
            });
        }
    });

    return symmetryAtoms;
}

export function getElementLociInfo(loci: Loci) {
    if (loci.kind !== 'element-loci') {
        return;
    }
    const stats = StructureElement.Stats.ofLoci(loci);
    const location = stats.elementCount ? stats.firstElementLoc : stats.firstStructureLoc;
    const x = StructureProperties.atom.x(location);
    const y = StructureProperties.atom.y(location);
    const z = StructureProperties.atom.z(location);
    // const sourceIndex = StructureProperties.atom.sourceIndex(location)
    const type_symbol = StructureProperties.atom
        .type_symbol(location)
        .split('')
        .map((s, i) => (i === 0 ? s : s.toLowerCase()))
        .join('');

    return {
        index: location.element,
        element: type_symbol,
        // color: getElementColor(type_symbol),
        x,
        y,
        z,
    };
}

export function getCleavageSurf(params: MaterialCleaveParams, origin: MaterialItem) {
    const { lattice } = origin;
    if (!lattice) {
        return;
    }
    const { matrix } = lattice;
    const { h, k, l, depth } = params;
    const [coefficient, cellVec] = getSurfaceVector(
        matrix[0] as [number, number, number],
        matrix[1] as [number, number, number],
        matrix[2] as [number, number, number],
        h,
        k,
        l
    );
    const bulk = material2Bulk(origin)!;
    const surf = buildBulk(bulk, coefficient, depth, true);

    return surf;
}

export function bulk2Material(bulk: Bulk) {
    const material: MaterialItem = {
        expand: [1, 1, 1],
        atoms: [],
        lattice: undefined,
    };
    const cell = bulk.getCell();
    let lattice: Lattice | undefined = undefined;

    if (cell) {
        const [a, b, c, alpha, beta, gamma] = cellToCellpar(cell);
        lattice = createLatticeByParams({
            spacegroup: {
                symbol: 'P 1',
                no: 1,
            },
            matrix: cell,
            a,
            b,
            c,
            alpha,
            beta,
            gamma,
        });
    }

    const symbols = bulk.getSymbols();
    const xyzs = bulk.getCoordinates();
    const abcs = bulk.getFractionalCoordinates() as number[][];
    const atoms = symbols.map((element, index) => {
        const atom = createAtom(
            {
                element,
                xyz: xyzs[index],
                abc: abcs[index],
            },
            {
                lattice,
                order: index,
            }
        );
        return atom;
    });

    material.lattice = lattice;
    material.atoms = atoms;
    return material;
}

export function material2Bulk(material: MaterialItem) {
    const { lattice, atoms } = material;
    if (!lattice) {
        return;
    }
    const cell = [lattice.vecA, lattice.vecB, lattice.vecC];
    const symbols: string[] = [];
    const position: number[][] = [];
    const fracPosition: number[][] = [];
    atoms.forEach(atom => {
        symbols.push(atom.element);
        position.push(atom.xyz);
        fracPosition.push(atom.abc!);
    });
    const bulk = new Bulk(cell, symbols, position, fracPosition);
    return bulk;
}

export function getElementColor(
    element: string,
    params?: {
        biology?: boolean;
        extraColorTable?: { [k: string]: number };
    }
) {
    const { biology, extraColorTable = {} } = params || {};
    if (biology) {
        return `#${{ ...ElementSymbolColors, C: 0x48e533 }[
            element.toUpperCase() as keyof typeof ElementSymbolColors
        ].toString(16)}`;
    }

    const el = element.toUpperCase();

    const color = extraColorTable[el] || (VESTA_COLOR_TABLE as { [key: string]: number })[el];
    const rgb = Color.toRgb(Color(color));
    return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

export function getVertexByVectors(vectors: number[][]) {
    const a = vectors[0];
    const b = vectors[1];
    const c = vectors[2];
    const p0 = [0, 0, 0];
    const p1 = a;
    const p2 = b;
    const p3 = add(a, b);
    const p4 = c;
    const p5 = add(a, c);
    const p6 = add(b, c);
    const p7 = add(add(a, b), c);

    return [p0, p1, p2, p3, p4, p5, p6, p7];
}

export function getPointsByVertex(vertex: number[][]) {
    const [p0, p1, p2, p3, p4, p5, p6, p7] = vertex;

    return [
        [p0, p1],
        [p0, p2],
        [p1, p3],
        [p2, p3],
        [p0, p4],
        [p1, p5],
        [p2, p6],
        [p3, p7],
        [p4, p5],
        [p4, p6],
        [p5, p7],
        [p6, p7],
    ];
}

export function ase2Material(ase: ASEDataItem): MaterialItem {
    const { length, angle, chemical_formula, matrix, spacegroup: aseSpacegroup = [1, 'P1'], atoms: aseAtoms } = ase;
    const material: MaterialItem = {
        expand: [1, 1, 1],
        atoms: [],
        lattice: undefined,
    };

    const lattice = (() => {
        const spacegroup = {
            symbol: aseSpacegroup[1],
            no: aseSpacegroup[0],
        };
        if (matrix) {
            const [a, b, c, alpha, beta, gamma] = cellToCellpar(matrix);
            return createLatticeByParams({
                spacegroup,
                matrix,
                a,
                b,
                c,
                alpha,
                beta,
                gamma,
            });
        }
        if (!length || !angle) {
            return;
        }
        const [a, b, c] = length;
        const [alpha, beta, gamma] = angle;
        const lattice = createLatticeByParams({
            spacegroup,
            a,
            b,
            c,
            alpha,
            beta,
            gamma,
        });
        return lattice;
    })();

    const atoms = aseAtoms.map((item, index) => {
        const params = {
            element: item.formula,
            xyz: item.cart_coord,
            abc: item.frac_coord,
            moveFlag: item.move_flag,
            id: item.id,
        };
        const atom = createAtom(params, {
            lattice,
            order: index,
        });

        return atom;
    });

    material.lattice = lattice;
    material.atoms = atoms;
    material.chemicalFormula = chemical_formula;
    return material;
}

export function material2Ase(material: MaterialItem) {
    const { atoms: matAtoms, lattice } = material;
    const ase: ASEDataItem = {
        atoms: [],
    };
    matAtoms.forEach(item => {
        ase.atoms.push({
            cart_coord: item.xyz,
            formula: item.element,
            frac_coord: item.abc!,
            id: item.id,
            move_flag: item.moveFlag,
        });
    });
    if (!lattice) {
        return ase;
    }
    const { a, b, c, alpha, beta, gamma, matrix, spacegroup } = lattice;
    ase.angle = [alpha, beta, gamma];
    ase.length = [a, b, c];
    ase.spacegroup = [spacegroup.no, spacegroup.symbol];
    ase.matrix = matrix;

    return ase;
}

export function angle2matrix3(angle: number, axis: number[]) {
    let cos = Math.cos(angle);
    let sin = Math.sin(angle);
    let [x, y, z] = axis;
    return [
        [cos + x * x * (1 - cos), x * y * (1 - cos) - z * sin, x * z * (1 - cos) + y * sin],
        [y * x * (1 - cos) + z * sin, cos + y * y * (1 - cos), y * z * (1 - cos) - x * sin],
        [z * x * (1 - cos) - y * sin, z * y * (1 - cos) + x * sin, cos + z * z * (1 - cos)],
    ];
}

export function rotatePoints(params: { points: number[][]; matrix3: number[][] }) {
    const { points, matrix3 } = params;
    const center = points.reduce((a, b) => add(a, b)).map(n => divide(n, points.length));
    const relativePoints = points.map(p => subtract(p, center));
    const result = relativePoints.map(p => add(multiply(matrix3, p) as number[], center));
    return result;
}

export function delMaterialAtoms(material: MaterialItem, ids: number[]) {
    material.atoms = material.atoms.filter(atom => !ids.includes(atom.order!));
    return material;
}

export function addMaterialAtoms(material: MaterialItem, params: AtomParams[]) {
    const start = material.atoms.length;
    params.forEach((p, i) => {
        const atom = createAtom(p, {
            lattice: material.lattice,
            order: start + i,
        });
        material.atoms.push(atom);
    });
    return material;
}

export async function readFileText(file: File): Promise<string> {
    return new Promise(resolve => {
        const reader = new FileReader();
        reader.onload = (ev: ProgressEvent<FileReader>) => {
            const result = ev?.target?.result || '';
            resolve(result as string);
        };
        reader.readAsText(file);
    });
}

export async function readFileArrayBuffer(file: File): Promise<ArrayBuffer> {
    return new Promise(resolve => {
        const reader = new FileReader();
        reader.onload = (ev: ProgressEvent<FileReader>) => {
            const result = ev?.target?.result as ArrayBuffer;
            resolve(result);
        };
        reader.readAsArrayBuffer(file);
    });
}

export function CellPeriod(
    cellVector: number[][],
    cartCoords: number[][],
    elements: string[],
    x: number,
    y: number,
    z: number
) {
    let { cartCoords: cartCoords1, elements: elements1 } = moveAtomsAlongCellVector(
        cartCoords,
        elements,
        cellVector[0],
        x
    );
    let { cartCoords: cartCoords2, elements: elements2 } = moveAtomsAlongCellVector(
        cartCoords1,
        elements1,
        cellVector[1],
        y
    );
    let { cartCoords: cartCoords3, elements: elements3 } = moveAtomsAlongCellVector(
        cartCoords2,
        elements2,
        cellVector[2],
        z
    );
    return { cartCoords: cartCoords3, elements: elements3 };
}

function moveAtomsAlongCellVector(cartCoords: number[][], elements: string[], cellVector: number[], multiply: number) {
    let newCartCoords: number[][] = [];
    let newElements: string[] = [];
    const atomsNum = cartCoords.length;
    for (let i = 1; i < multiply; i++) {
        const multiplyVector = cellVector.map(n => n * i);
        for (let j = 0; j < atomsNum; j++) {
            newCartCoords.push(add(cartCoords[j], multiplyVector));
        }
        newElements = newElements.concat(elements);
    }
    console.log('elements', cartCoords.concat(newCartCoords), newCartCoords);
    return { cartCoords: cartCoords.concat(newCartCoords), elements: elements.concat(newElements) };
}

export function CellVectorPeriod(lattice: Lattice, x: number, y: number, z: number) {
    let points = getVertexByVectors(lattice.matrix);
    let edges = getPointsByVertex(points);
    edges = moveCellEdgeAlongCellVector(edges, lattice.matrix[0], x);
    edges = moveCellEdgeAlongCellVector(edges, lattice.matrix[1], y);
    edges = moveCellEdgeAlongCellVector(edges, lattice.matrix[2], z);
    return edges;
}

function moveCellEdgeAlongCellVector(edges: number[][][], cellVector: number[], multiply: number) {
    let newEdges = [];
    const edgesNum = edges.length;
    for (let i = 1; i < multiply; i++) {
        const multiplyVector = cellVector.map(n => n * i);
        for (let j = 0; j < edgesNum; j++) {
            let edge = edges[j];
            let newEdge = edge.map(point => add(point, multiplyVector));
            newEdges.push(newEdge);
        }
    }
    return edges.concat(newEdges);
}

export function cellRedefine(cellMatrix: number[][], coeffs: number[][]) {
    let newCellMatrix = multiply(coeffs, cellMatrix);
    let a = norm(newCellMatrix[0]).valueOf() as number;
    let b = norm(newCellMatrix[1]).valueOf() as number;
    let c = norm(newCellMatrix[2]).valueOf() as number;
    let alpha = ((acos(dot(newCellMatrix[1], newCellMatrix[2]) / (b * c)).valueOf() as number) * 180) / Math.PI;
    let beta = ((acos(dot(newCellMatrix[0], newCellMatrix[2]) / (a * c)).valueOf() as number) * 180) / Math.PI;
    let gamma = ((acos(dot(newCellMatrix[0], newCellMatrix[1]) / (a * b)).valueOf() as number) * 180) / Math.PI;
    return [a, b, c, alpha, beta, gamma];
}
