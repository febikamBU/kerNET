"""
©Copyright 2020 University of Florida Research Foundation, Inc. All rights reserved.
Licensed under the CC BY-NC-SA 4.0 license (https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode).
"""
import time
import logging

import torch


logger = logging.getLogger()

def train(opt, n_epochs, trainer, loader, val_loader, criterion, device):
  logger.info('Starting training...')

  total_epoch = trainer.start_epoch + n_epochs
  total_batch = len(loader)

  for epoch in range(trainer.start_epoch, total_epoch):
    running_loss = 0.
    running_acc = 0.
    running_time = 0.
    for batch, (input, target) in enumerate(loader):

      # train step
      start = time.time()
      input, target = \
        input.to(device, non_blocking=True), target.to(device, non_blocking=True)
      output, loss = trainer.step(input, target, criterion)
      end = time.time()

      # get some batch statistics
      _, predicted = torch.max(output, 1)
      acc = 100 * (predicted == target).sum().to(torch.float).item() / target.size(0)
      trainer.log_loss_values({
        'train_batch_{}'.format(criterion.__class__.__name__.lower()): loss,
        'train_batch_acc': acc
      })

      # print statistics
      running_loss += loss
      running_acc += acc
      running_time += end - start
      if batch % opt.print_freq == opt.print_freq - 1:
        message = '[epoch: %d/%d, batch: %5d/%d] loss (%s): %.3f, acc (%%): %.3f, runtime (s): %.3f' % (
          epoch + 1, total_epoch, batch + 1, total_batch,
          criterion.__class__.__name__.lower(),
          running_loss / opt.print_freq,
          running_acc / opt.print_freq,
          running_time / opt.print_freq
        )
        logger.info(message)

        running_loss = 0.
        running_acc = 0.
        running_time = 0.

    # validate
    if epoch % opt.val_freq == opt.val_freq - 1:
      if hasattr(trainer, 'update_centers_eval'):
        trainer.update_centers_eval()
      correct, total = 0, 0
      total_batch_val = len(val_loader)
      for i, (input, target) in enumerate(val_loader):
        logger.info('batch: {}/{}'.format(i + 1, total_batch_val))
        input, target = \
          input.to(device, non_blocking=True), target.to(device, non_blocking=True)
        output = trainer.get_eval_output(input)

        _, predicted = torch.max(output, 1)
        correct += (predicted == target).sum().item()
        total += target.size(0)

      acc = 100 * correct / total
      trainer.log_loss_values({
        'val_acc': acc
      })

      message = '[epoch: %d] val acc (%%): %.3f' % (
        epoch + 1, acc)
      logger.info(message)
      if opt.schedule_lr:
        trainer.scheduler_step(acc)
      trainer.save(epoch, acc)

  logger.info('Training finished!')
