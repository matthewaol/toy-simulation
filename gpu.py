
import numpy as np
import pyopencl as cl
import pyopencl.array as clarray

def get_context_queue(name="V100"):
    #   list the platforms
    platforms = cl.get_platforms()
    print("Found platforms (will use first listed):", platforms)
    #   select the gpu
    my_gpu = platforms[0].get_devices(
        device_type=cl.device_type.GPU)
    assert (my_gpu)
    print("Found GPU(s):", my_gpu)
    my_gpu = [g for g in my_gpu if name in str(g)]
    print("Will use GPU", my_gpu[0])
    #   create the context for the gpu, and the corresponding queue
    context = cl.Context(devices=my_gpu)
    queue = cl.CommandQueue(context)
    return context, queue


phase_sum_kernel="""
__kernel void phase_sum(__global double* q_vecs, __global double* atom_vecs, int num_atoms,
    __global double* real_out, __global double* imag_out) {
   // fill in!
}

"""

class GPUHelper:

    def __init__(self, Q, context, queue):
        self.dt = np.float64
        self.queue = queue
        self.context = context

        self.q_vecs = self.flatten(Q)  # q vectors host array
        self.real_out = self.flatten(np.zeros(len(Q)))
        self.imag_out = self.flatten(np.zeros(len(Q)))

        self.q_dev = None  # q vectors device array
        self.real_out_dev = None  # real output device array
        self.imag_out_dev = None  # imag output device array

        self._allocate_arrays()

        # phase_sum_kernel is the string
        self.program = cl.Program(self.context, phase_sum_kernel).build()
        self.program.phase_sum.set_scalar_arg_dtypes([None, None, np.int32, None, None])

    def flatten(self, np_vec):
        np_vec_1d = np_vec.ravel().astype(self.dt)
        return np.ascontiguousarray(np_vec_1d)

    def _allocate_arrays(self):
        self.q_dev = clarray.to_device(self.queue, self.q_vecs)
        self.real_out_dev = clarray.to_device(self.queue, self.real_out)
        self.imag_out_dev = clarray.to_device(self.queue, self.imag_out)

    def phase_sum(self, atoms):
        num_atoms = len(atoms)
        atoms_dev = clarray.to_device(self.queue, self.flatten(atoms))

        # run kernel
        # ... ...
        num_pix = int(len(self.q_vecs) / 3.)
        self.program.phase_sum(self.queue, (num_pix,), None,
                               self.q_dev.data,
                               atoms_dev.data,
                               np.int32(num_atoms),
                               self.real_out_dev.data, self.imag_out_dev.data)

        # copy real/imag results back to host arrays
        cl.enqueue_copy(self.queue, self.real_out, self.real_out_dev)
        cl.enqueue_copy(self.queue, self.imag_out, self.imag_out_dev)

        # return real,imag parts:

        # TODO: de-allocate atoms_dev  (delete it from the GPU)

        return self.real_out, self.imag_out
