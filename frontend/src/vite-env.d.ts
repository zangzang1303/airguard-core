/// <reference types="vite/client" />

import "react";

// @types/react 18 chưa khai báo thuộc tính `inert` (chỉ có từ React 19).
// React 18 truyền thẳng giá trị chuỗi xuống DOM nên dùng `inert=""` để bật, `undefined` để tắt.
declare module "react" {
  interface HTMLAttributes<T> {
    inert?: "" | undefined;
  }
}
