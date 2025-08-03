import { create } from 'zustand';

type ButtonControlState = {
    /** 全局按钮禁用状态 */
    isButtonsDisabled: boolean;
    /** 切换所有按钮状态 */
    toggleButtons: () => void;
    /** 直接设置按钮状态 */
    setButtonsState: (state: boolean) => void;
    /** 设置旋转角度 */
    setRotationAngle: (angle: number) => void;
    /** 旋转角度 */
    rotationAngle: number;
    /** 文件类型 */
    fileFormat: string;
    /** 设置文件类型 */
    setFileFormat: (file: string) => void;

    customizedUnit: boolean;
    setCustomizedUnit: (state: boolean) => void;

    headAtom: any;
    setHeadAtom: (statle: any) => void;

    tailAtom: any;
    setTailAtom: (statle: any) => void;

    color: string;
    setColor: (color: string) => void;

    bondStatus: boolean;
    setBondStatus: (state: boolean) => void;
};

export const useButtonControlStore = create<ButtonControlState>(set => ({
    isButtonsDisabled: false,
    fileFormat: '',
    rotationAngle: 45, // 默认弧度
    customizedUnit: true,
    headAtom: null,
    tailAtom: null,
    color: '#f4f6fb',
    bondStatus: true,
    /** 设置颜色 */
    setColor: color => set({ color }),
    /** 切换所有按钮状态 */
    toggleButtons: () =>
        set(state => ({
            isButtonsDisabled: !state.isButtonsDisabled,
        })),
    setButtonsState: state => set({ isButtonsDisabled: state }),

    setRotationAngle: angle =>
        set({
            rotationAngle: angle,
        }),

    setFileFormat: file => set({ fileFormat: file }),

    setCustomizedUnit: state => set({ customizedUnit: state }),

    setHeadAtom: state => set({ headAtom: state }),
    setTailAtom: state => set({ tailAtom: state }),

    setBondStatus: state => set({ bondStatus: state }),
}));
